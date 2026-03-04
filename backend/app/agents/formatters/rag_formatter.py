from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """Canonical chunk representation."""
    file_id: UUID = Field(description='ID of the file from which the chunk was obtained.')
    page: str = Field(description='page label for the page where the chunk text lies. Must be a string')
    text: str = Field(description='actual text of the chunk.')

class RagOutput(BaseModel):
    """Canonical output of the RAG agent"""
    chunks: list[Chunk] = Field(description='a list of the retrieved chunks.')
