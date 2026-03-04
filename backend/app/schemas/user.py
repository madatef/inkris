from datetime import datetime
import re
from typing import Annotated

from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import PasswordPolicy


class UserCreate(BaseModel): 
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=20)]
    first_name: Annotated[str, Field(min_length=1, max_length=100)]
    last_name: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate input meets our password policy.
        """
        valid, error = PasswordPolicy.validate(v)
        if not valid:
            raise ValueError(error)
        return v


    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str, info) -> str:
        """
        Validate name fields:
        - Not empty or only whitespace
        - Contains at least one alphabetic character
        - No leading/trailing whitespace
        - Not unreasonably long
        """
        # Strip whitespace
        v = v.strip()
        
        # Check if empty after stripping
        if not v:
            raise ValueError(f'{info.field_name} cannot be empty or only whitespace')
        
        # Check for at least one alphabetic character
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError(f'{info.field_name} must contain at least one letter')
        
        # Allow only leading alphabetic chars 
        if not re.match(r'[a-zA-Z]', v[0]):
            raise ValueError(f'{info.field_name} must start with a letter')
        

        # This allows only letters, spaces, hyphens, and apostrophes, and periods
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v):
            raise ValueError(f'{info.field_name} contains invalid characters')
        
        # Check for excessive length of individual words (potential spam/abuse)
        words = v.split()
        for word in words:
            if len(word) > 20:
                raise ValueError(f'{info.field_name} contains unreasonably long words')
        
        return v[0].upper() + v[1:] # capitalize first letter

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime 

    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy models
        populate_by_name = True # Allows aliases
