from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, Field, model_validator, field_validator

from app.core.enums import FileStatusEnum, FileExtensionEnum
from app.storage.base import UploadSpec


class FilePresigned(BaseModel):
    name: str
    extension: FileExtensionEnum
    description: Optional[str] = None
    size_bytes: int

    @field_validator("name", mode="before")
    @classmethod
    def nonempty_name_check(cls, v):
        if not v.strip():
            raise ValueError("File name can't be empty.")
        return v

class FileComplete(BaseModel):
    success: bool
    
class FileUpdate(BaseModel):
    name: Annotated[str, Field(min_length=1)] | None = None
    description: str | None = None


    @model_validator(mode='after')
    def nullity_check(self):
        if self.name is None and self.description is None:
            raise ValueError("At lease one value should be provided to update the file.")
        return self
    
    @field_validator("name", mode="before")
    @classmethod
    def nonempty_name_check(cls, v):
        if v is not None and not v.strip():
            raise ValueError("File name can't be empty.")
        return v

class PresignedResponse(BaseModel):
    file_id: UUID
    upload: UploadSpec

class CompleteResponse(BaseModel):
    success: bool
    message: str

class FileResponse(BaseModel):
    id: UUID
    name: str
    extension: FileExtensionEnum
    size_bytes: int
    description: str | None
    status: FileStatusEnum
    created_at: datetime
    updated_at: datetime 
    deleted_at: datetime | None

    class Config:
        # Parse SQLAlchemy models
        from_attributes = True
        populate_by_name = True
