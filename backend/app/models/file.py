from datetime import datetime
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Index, String, Enum, ForeignKey, Integer, text

from app.models.base import BaseModel
from app.core.enums import FileExtensionEnum, FileStatusEnum

class File(BaseModel):

    __tablename__ = "files"

    name: Mapped[str] = mapped_column(String, nullable=False)

    extension: Mapped[FileExtensionEnum] = mapped_column(
        Enum(
            FileExtensionEnum,
            name="extension_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[FileStatusEnum] = mapped_column(
        Enum(
            FileStatusEnum,
            name="file_status_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=FileStatusEnum.PENDING,
    )

    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    processing_error: Mapped[str | None] = mapped_column(String, nullable=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "uq_user_file",
            "name",
            "extension",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    user = relationship("User", back_populates="files")
    file_metadata = relationship("ExcelMetadata", back_populates='file')