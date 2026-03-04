from typing import Annotated, List
from uuid import UUID

from fastapi import Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.file import File
from app.models.conversation import Conversation
from app.core.auth import decode_access_token
from app.core.error_registry import (
    CONVERSATION_DELETED,
    CONVERSATION_FORBIDDEN,
    CONVERSATION_NOT_FOUND,
    FILE_DELETED,
    FILE_FORBIDDEN,
    FILE_NOT_FOUND,
    INVALID_TOKEN,
)
from app.core.errors import AppError


# Generator for database sessions
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve the currently authenticated user from the JWT.
    """
    token = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]

    if not token:
        token = request.cookies.get('access_token')
    
    if not token:
        raise AppError(INVALID_TOKEN)

    user_id = decode_access_token(token)

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AppError(INVALID_TOKEN)
    return user

async def get_file(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    id: str = Path(...),
) -> File:
    """
    Get a file by ID

    Returns:
        File instance with all DB fields
    """
    try:
        typed = UUID(id)
    except ValueError:
        raise AppError(FILE_NOT_FOUND)
    file: File | None = await session.get(File, typed)
    
    if file is None: 
        raise AppError(FILE_NOT_FOUND)
    if not file.user_id == user.id:
        raise AppError(FILE_FORBIDDEN)
    if file.deleted_at is not None:
        raise AppError(FILE_DELETED)
    
    return file

async def get_user_files(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[File]:
    stmt = select(File).where(File.user_id == user.id, File.deleted_at == None )
    result = await session.execute(stmt)
    files = result.scalars().all()
    return files

async def get_current_conversation(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    id: str = Path(...),
) -> Conversation:
    conv: Conversation | None = await session.get(Conversation, UUID(id))
    if conv is None:
        raise AppError(CONVERSATION_NOT_FOUND)
    if conv.user_id != user.id:
        raise AppError(CONVERSATION_FORBIDDEN)
    if conv.deleted_at is not None:
        raise AppError(CONVERSATION_DELETED)
    return conv