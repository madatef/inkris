from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.files import create_file, complete_upload, update_file, delete_file
from app.core.deps import get_db, get_current_user, get_file, get_user_files
from app.schemas.file import (
    CompleteResponse,
    FilePresigned,
    PresignedResponse,
    FileComplete,
    FileResponse,
    FileUpdate,
)
from app.models.file import File
from app.models.user import User
from app.tasks.queue import enqueue_file_processing
from app.storage.s3_provider import s3

router = APIRouter(prefix="/files", tags=["files", "library"])

@router.get("/my-files", response_model=List[FileResponse])
async def get_user_files(files: List[File] = Depends(get_user_files)):
    return files

@router.post("/presigned-upload", response_model=PresignedResponse, status_code=201)
async def create_presigned_url(
    data: FilePresigned,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file_id, upload = await create_file(
        session,
        user_id=user.id,
        data=data,
    )
    await session.commit()
    return PresignedResponse(file_id=file_id, upload=upload)

@router.post("/upload-completion/{id}", response_model=CompleteResponse)
async def completion(
    data: FileComplete,
    session: AsyncSession = Depends(get_db),
    file: File = Depends(get_file),
):
    if not data.success:
        return CompleteResponse(
            success=False,
            message="Then try uploading again!",
        )
    
    uploaded = await complete_upload(
        session,
        file=file,
    )

    if uploaded.get("already_completed"):
        return CompleteResponse(
            success=True,
            message="Upload already completed.",
        )
    
    enqueue_file_processing(file_id=file.id)

    await session.commit()
    return CompleteResponse(
        success=True,
        message="File uploaded successfully.",
    )

@router.patch("/{id}", response_model=FileResponse)
async def update(
    data: FileUpdate,
    file: File = Depends(get_file),
    session: AsyncSession = Depends(get_db),
) -> File:

    name = data.name
    description = data.description

    # fallback to original values
    if not name.strip():
        name = file.name
    
    if not description.strip():
        description = file.description

    updated = await update_file(
        session,
        file=file,
        name=name,
        description=description,
    )
    await session.commit()
    return updated

@router.delete("/{id}", response_model=FileResponse)
async def delete(
    file: File = Depends(get_file),
    session: AsyncSession = Depends(get_db),
) -> File:
    res = await delete_file(session, file=file)
    await session.commit()
    return res

@router.get('/download/{id}')
async def download_file(file: File = Depends(get_file)):
    return s3.create_presigned_download(file_id=file.id)