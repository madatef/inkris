from io import BytesIO

import pandas as pd

from app.core.logger import logger
from app.models.file import File
from app.models.excel_metadata import ExcelMetadata
from app.core.enums import FileExtensionEnum
from app.core.events.redis import publish
from app.core.events.types import FileProcessingEvent
from app.storage.s3_provider import s3
from app.db.session import SyncSessionLocal
from app.services.transformers.base import bytes_to_pages
from app.services.transformers.chunkers import llamaindex_sentence_splitter
from app.services.transformers.embedders import openai_text_small
from app.vector_store.qdrant import qdrant_store
from app.config import settings
from app.core.enums import LlamaIndexSplitterEnum


def process_document(file: File) -> None:
    logger.info(f"Processing document: {file.id}")
    publish(FileProcessingEvent(
        file_id=file.id,
        user_id=file.user_id,
        status="processing",
        progress=1,
    ))

    ingest_docs(file)
    publish(FileProcessingEvent(
    file_id=file.id,
    user_id=file.user_id,
    status="processing",
    progress=99,
    ))

def process_excel(file: File) -> None:
    logger.info(f"Processing excel: {file.id}")
    publish(FileProcessingEvent(
        file_id=file.id,
        user_id=file.user_id,
        status="processing",
        progress=1,
    ))

    obj = s3.client.get_object(
        Bucket=s3.bucket_name,
        Key=str(file.id),
    )
    publish(FileProcessingEvent(
        file_id=file.id,
        user_id=file.user_id,
        status="processing",
        progress=20,
    ))

    raw_bytes = obj["Body"].read()
    excel = pd.ExcelFile(BytesIO(raw_bytes))
    sheet_names = excel.sheet_names

    meta = {"sheet_names": sheet_names}
    meta_record = ExcelMetadata(file_metadata=meta, file_id=file.id)

    with SyncSessionLocal() as session:
        session.add(meta_record)
        session.commit()
    publish(FileProcessingEvent(
        file_id=file.id,
        user_id=file.user_id,
        status="processing",
        progress=30,
    ))

    step = 70 // len(sheet_names)

    for i, sheet_name in enumerate(sheet_names):
        df = excel.parse(sheet_name)

        parquet_buffer = BytesIO()
        df.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0)

        key = f"{file.id}/{sheet_name}.parquet"
        s3.client.upload_fileobj(parquet_buffer, s3.bucket_name, key)

        publish(FileProcessingEvent(
            file_id=file.id,
            user_id=file.user_id,
            status="processing",
            progress=min(20 + (i+1) * step, 99),
        ))

# Helper for file ingestion
def ingest_docs(file: File) -> None:
    obj = s3.client.get_object(
        Bucket=s3.bucket_name,
        Key=str(file.id),
    )
    publish(FileProcessingEvent(
        file_id=file.id,
        user_id=file.user_id,
        status="processing",
        progress=10,
    ))
    raw_bytes = obj["Body"].read()

    pages = bytes_to_pages(file=file, raw_bytes=raw_bytes)
    publish(FileProcessingEvent(
        file_id=file.id,
        user_id=file.user_id,
        status="processing",
        progress=25,
    ))

    #TODO: add images, tables, and entities extraction logic
    
    points = llamaindex_sentence_splitter.pages_to_points(
        pages=pages,
        splitter=LlamaIndexSplitterEnum.SENTENCE,
        embedder=openai_text_small,
    )
    publish(FileProcessingEvent(
        file_id=file.id,
        user_id=file.user_id,
        status="processing",
        progress=50,
    ))

    qdrant_store.upload(
        collection=settings.QDRANT_COLLECTION,
        points=points,
    )
