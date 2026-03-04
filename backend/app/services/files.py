from typing import Any
from uuid import UUID

from botocore.exceptions import ClientError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.config import settings
from app.core.errors import AppError
from app.core.error_registry import (
    FILE_DELETED,
    FILE_NAME_EXISTS,
    FILE_NOT_RECEIVED,
    FILE_UPLOAD_INVALID,
    FILE_UPLOADED,
    QUOTA_EXCEEDED_FILE_PROCESSING,
    QUOTA_EXCEEDED_FILES,
    QUOTA_EXCEEDED_STORAGE,
    QUOTA_NOT_FOUND,
)
from app.core.enums import FileStatusEnum
from app.core.logger import logger
from app.models.file import File
from app.models.quota import Quota
from app.schemas.file import FilePresigned
from app.core.files import EXTENSION_TO_MIME
from app.storage.s3_provider import s3
from app.vector_store.qdrant import qdrant_store
from app.vector_store.base import VectorFilter
from app.models.conversation import Conversation


async def create_file(
    session: AsyncSession,
    *,
    user_id: UUID,
    data: FilePresigned,
) -> tuple[UUID, dict[str, Any]]: 
    """
    Create and persist file metadata

    Returns: 
        File record details
    
    Raises:
        FileNameExistsError: if file with the same and extension exists

    """
    if data.size_bytes > settings.MAX_FILE_SIZE_BYTES:
        raise AppError(FILE_UPLOAD_INVALID)

    quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
    quota_res = await session.execute(quota_stmt)
    quota = quota_res.scalar_one_or_none()
    if quota is None:
        raise AppError(QUOTA_NOT_FOUND)

    if quota.files < 1:
        raise AppError(QUOTA_EXCEEDED_FILES)
    if quota.storage_bytes < data.size_bytes:
        raise AppError(QUOTA_EXCEEDED_STORAGE)
    if quota.file_processing < 1:
        raise AppError(QUOTA_EXCEEDED_FILE_PROCESSING)


    # Check if other files with the same name and extension exist
    stmt = select(File).where(
        File.name == data.name,
        File.extension == data.extension,
        File.user_id == user_id,
        File.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise AppError(FILE_NAME_EXISTS)
    
    file = File(
        name=data.name,
        extension=data.extension,
        user_id=user_id,
        description=data.description,
        size_bytes=data.size_bytes,
    )
    session.add(file)

    try:
        quota.files -= 1
        quota.storage_bytes -= data.size_bytes
        await session.flush([file, quota])
    except IntegrityError:
        # safety net for race conditions
        await session.rollback()
        raise AppError(FILE_NAME_EXISTS)

    await session.refresh(file)
    
    content_type = EXTENSION_TO_MIME[data.extension]
    upload = s3.create_presigned_upload(
        file_id=file.id,
        size_bytes=data.size_bytes,
        content_type=content_type,
    )

    return file.id, upload

async def complete_upload(
    session: AsyncSession,
    *,
    file: File,
) -> dict:
    if file.deleted_at is not None:
        raise AppError(FILE_DELETED)
    
    # Idempotency guarantee
    if file.status in {
        FileStatusEnum.UPLOADED,
        FileStatusEnum.PROCESSING,
        FileStatusEnum.READY,
    }:
        return {"already_completed": True}

    if file.status != FileStatusEnum.PENDING:
        raise AppError(FILE_UPLOADED)

    try:
        head = s3.client.head_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=str(file.id),
        )
    except ClientError:
        raise AppError(FILE_NOT_RECEIVED)
        
    if (
        head.get("ContentLength") != file.size_bytes
        or head.get("ContentType") != EXTENSION_TO_MIME[file.extension]
    ):
        try:
            s3.client.delete_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=str(file.id),
            )
        except Exception as e:
            print(f"\nFailed to delete S3 file: {str(file.id)}\nerror: {str(e)}\n\n")
        raise AppError(FILE_UPLOAD_INVALID)
 
    file.status = FileStatusEnum.UPLOADED
    await session.flush([file])
    await session.refresh(file)
    return {"success": True}

async def update_file(
    session: AsyncSession,
    *,
    file: File,
    name: str,
    description: str | None = None,
) -> File:
    
    if file.deleted_at is not None:
        raise AppError(FILE_DELETED)
    
    # Check if other files with the same name and extension exist
    precheck = select(File).where(
        File.name == name,
        File.extension == file.extension,
        File.user_id == file.user_id,
        File.deleted_at is None,
        File.id != file.id,
    )
    result = await session.execute(precheck)
    duplicate: File | None = result.scalar_one_or_none()
    if duplicate is not None:
        raise AppError(FILE_NAME_EXISTS)
    
    file.name, file.description = name, description

    try:
        await session.flush([file])
    except IntegrityError:
        await session.rollback()
        raise AppError(FILE_NAME_EXISTS)

    await session.refresh(file)
    return file

async def delete_file(
    session: AsyncSession,
    *,
    file: File,
) -> File:

    # Make deletion idempotent
    if file.deleted_at is not None:
        return file

    quota_stmt = select(Quota).where(Quota.user_id == file.user_id).with_for_update()
    quota = (await session.execute(quota_stmt)).scalar_one_or_none()
    if quota is not None:
        quota.files += 1
        quota.storage_bytes += file.size_bytes

    conv_stmt = select(Conversation).where(Conversation.file_id == file.id)
    conversations = (await session.execute(conv_stmt)).scalars().all()
    for conv in conversations:
        conv.deleted_at = func.now()

    try:
        s3.client.delete_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=str(file.id),
        )
    except Exception as e:
        logger.warning(
            "Failed to delete S3 object",
            extra={"file_id": str(file.id), "error": str(e)},
        )
        
    # ---- VECTOR CLEANUP ----
    try:
        qdrant_store.delete_by_filter(
            collection=settings.QDRANT_COLLECTION,
            filters=[
                VectorFilter(key="file_id", values=[str(file.id)]),
            ],
        )
    except Exception as e:
        logger.warning(
            "Failed to delete vectors",
            extra={"file_id": str(file.id), "error": str(e)},
        )
    
    file.deleted_at = func.now()
    await session.flush()
    await session.refresh(file)

    return file
