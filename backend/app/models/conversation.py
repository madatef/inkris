import uuid
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Enum, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel
from app.core.enums import ConversationScopeEnum, MessageRoleEnum


class Conversation(BaseModel):
    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scope: Mapped[ConversationScopeEnum] = mapped_column(
        Enum(
            ConversationScopeEnum,
            name="file_scope_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )
    user = relationship("User", back_populates="conversations")

    __table_args__ = (
        Index("ix_conversations_user_scope", "user_id", "scope"),
    )


class ConversationMessage(BaseModel):
    __tablename__ = "conversation_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRoleEnum] = mapped_column(
        Enum(
            MessageRoleEnum,
            name="conversation_role_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_conv_msg_conv_created", "conversation_id", "created_at"),
    )
