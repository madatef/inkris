from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ExcelMetadata(BaseModel):
    __tablename__ = 'excel_files_metadata'

    file_id: Mapped[UUID] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    file_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False)

    file = relationship('File', back_populates='file_metadata')