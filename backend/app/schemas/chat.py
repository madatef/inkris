from datetime import datetime
from typing import Optional
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import ConversationScopeEnum, MessageRoleEnum


class ConversationCreate(BaseModel):
    scope: ConversationScopeEnum = ConversationScopeEnum.STUDIO
    file_id: Optional[UUID] = None
    title: Optional[str] = None

    @model_validator(mode="after")
    def validate_scope(self):
        if self.scope == ConversationScopeEnum.FILE and self.file_id is None:
            raise ValueError("file_id is required when scope='file'")
        return self

class ConversationUpdate(BaseModel):
    title: str

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        
        if len(v) < 3 or len(v) > 100:
            raise ValueError('Title must be at least 3, at most 100 characters long')
        
        pattern = r'^[a-zA-Z0-9\s\-,.\'\(\)!?&:;]+$'
        if not re.match(pattern, v):
            raise ValueError(
                'Title must contain only alphanumeric characters, spaces, and common punctuation '
                '(dashes, commas, apostrophes, periods, parentheses, exclamation marks, question marks, ampersands, colons, semicolons)'
            )
        
        return v

class ConversationResponse(BaseModel):
    id: UUID
    scope: str
    file_id: Optional[UUID] = None
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

class UserConversationsRequest(BaseModel):
    page: int = Field(..., ge=1, description="Page number, must be at least 1")
    page_size: int = Field(..., ge=1, description="Page size, must be at least 1")

class UserConversationsResponse(BaseModel):
    page: int
    page_size: int
    total: int
    has_next: bool
    items: list[ConversationResponse]

class ConversationMessages(BaseModel):
    limit: int = Field(..., ge=1, description="Number of messages to retrieve, must be at least 1")
    cursor: Optional[datetime] = None

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRoleEnum
    content: str
    
    class Config:
        from_attributes = True
        populate_by_name = True

class ConversationMessagesResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: Optional[datetime]
    has_next: bool

class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)

class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
