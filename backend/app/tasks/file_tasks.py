from uuid import UUID

from celery import shared_task
from sqlalchemy import func, select, update

import app.db.model_registry  # noqa: F401
from app.models.file import File
from app.core.enums import FileStatusEnum, FileExtensionEnum
from app.core.logger import logger
from app.db.session import SyncSessionLocal
from app.vector_store.qdrant import qdrant_store
from app.vector_store.base import VectorFilter
from app.config import settings
from app.services.file_processor import process_document, process_excel
from app.core.events.redis import publish
from app.core.events.types import FileProcessingEvent
from app.models.quota import Quota


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_kwargs={"max_retries": 3},
    name="app.tasks.file_tasks.process_file",
)
def process_file(self, file_id: UUID) -> None:

    # Change DB state (pending/error -> processing)
    with SyncSessionLocal() as session:
        stmt = (
            update(File)
            .where(
                File.id == file_id,
                File.deleted_at.is_(None),
                File.status.in_([
                    FileStatusEnum.UPLOADED,
                    FileStatusEnum.ERROR,
                ]),
            )
            .values(
                status=FileStatusEnum.PROCESSING,
                processing_started_at=func.now(),
                processing_error=None,
            )
            .returning(File)
        )

        result = session.execute(stmt)
        file = result.scalar_one_or_none()
        if file is None:
            return
        file_extension = file.extension
        user_id = file.user_id

        session.commit()
        
    try:
        # ---- CLEANUP (idempotency guarantee) ----
        if file_extension not in [FileExtensionEnum.XLSX, FileExtensionEnum.XLS]:
            qdrant_store.delete_by_filter(
                collection=settings.QDRANT_COLLECTION,
                filters=[
                    VectorFilter(key="file_id", values=[str(file_id)]),
                ],
            )
            
            process_document(File(id=file_id, extension=file_extension, user_id=user_id))
        else:
            process_excel(File(id=file_id, extension=file_extension, user_id=user_id))

        with SyncSessionLocal() as session:
            session.execute(
                update(File)
                .where(File.id == file_id, File.status == FileStatusEnum.PROCESSING)
                .values(
                    status=FileStatusEnum.READY,
                    processing_completed_at=func.now(),
                )
            )
            quota_stmt = select(Quota).where(Quota.user_id == user_id).with_for_update()
            quota_res = session.execute(quota_stmt)
            quota = quota_res.scalar_one_or_none()
            if quota is not None:
                quota.file_processing -= 1
            session.commit()
        
        publish(FileProcessingEvent(
            file_id=file.id,
            user_id=file.user_id,
            status="ready",
            progress=100,
        ))

    except Exception as exc:
        logger.exception("File processing failed", extra={"file_id": file_id})
        with SyncSessionLocal() as session:
            session.execute(
                update(File)
                .where(File.id == file_id, File.status == FileStatusEnum.PROCESSING)
                .values(
                    status=FileStatusEnum.ERROR,
                    processing_error=str(exc),
                )
            )
            session.commit()
        
        publish(FileProcessingEvent(
            file_id=file.id,
            user_id=file.user_id,
            status="error",
            progress=100,
            error=str(exc),
        ))
