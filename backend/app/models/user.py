from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from app.models.base import BaseModel



class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    first_name: Mapped[str | None] = mapped_column(
        String,
        nullable= True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", uselist=False, cascade="all, delete-orphan")
    quota = relationship("Quota", back_populates="user", cascade="all, delete-orphan")
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
