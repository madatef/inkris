from abc import ABC, abstractmethod
from io import BytesIO
from typing import List
from uuid import UUID

import fitz
from pydantic import BaseModel

from app.core.enums import FileExtensionEnum
from app.vector_store.base import VectorPoint
from app.models.file import File

class PageMetadata(BaseModel):
    page_label: int | str
    user_id: UUID
    file_id: UUID

class FilePage:
    def __init__(
        self,
        *,
        text: str,
        metadata: PageMetadata,
    ):
        self.text = text
        self.metadata = metadata

def bytes_to_pages(
    *,
    raw_bytes: bytes | BytesIO,
    file: File,
) -> List[FilePage]:
    if file.extension == FileExtensionEnum.PDF:
        pdf = fitz.open(stream=raw_bytes, filetype="pdf")
        try:
            pages = []
            for page_num, page in enumerate(pdf):
                pages.append(
                    FilePage(
                        text=page.get_text(),
                        metadata=PageMetadata(
                            page_label=pdf.get_page_labels()[page_num] if pdf.get_page_labels() else page_num + 1,
                            user_id=file.user_id,
                            file_id=file.id,
                        )
                    )
                )
        finally:
            pdf.close()
        return pages
    
    elif file.extension in (FileExtensionEnum.TXT, FileExtensionEnum.MD):
        # Decode bytes to text
        if isinstance(raw_bytes, BytesIO):
            text = raw_bytes.read().decode('utf-8', 'backslashreplace')
        else:
            text = raw_bytes.decode('utf-8', 'backslashreplace')
        
        # Treat as single page unless page breaks exist
        page_texts = text.split('\f')  # Split by form feed character
        pages = []
        for page_num, page_text in enumerate(page_texts, start=1):
            pages.append(
                FilePage(
                    text=page_text,
                    metadata=PageMetadata(
                        page_label=page_num,
                        user_id=file.user_id,
                        file_id=file.id,
                    )
                )
            )
        
        return pages

    else:
        raise NotImplementedError(
            f"bytes_to_pages does not support extension {file.extension} yet"
        )

class Embedder(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        ...
    
class Chunker(ABC):
    def __init__(self, *, chunk_size: int, overlap: int):
        if overlap > chunk_size:
            raise ValueError("Chunk overlap can't exceed chunk size.")
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    @abstractmethod
    def pages_to_points(self, *, pages: List[FilePage], embedder: Embedder) -> List[VectorPoint]:
        ...