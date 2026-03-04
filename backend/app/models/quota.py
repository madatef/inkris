from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

class Quota(BaseModel):
    __tablename__ = "quotas"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    files: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5'))
    storage_bytes: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('104857600')) # 100 MB
    conversations: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10'))
    web_searches: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10'))
    web_scraping: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10'))
    image_generations: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5'))
    video_generations: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('2'))
    llm_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('50000'))
    file_processing: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10'))

    user = relationship("User", back_populates="quota")

    __table_args__ = (
        Index('ix_quotas_user_id', 'user_id'),
    )
    