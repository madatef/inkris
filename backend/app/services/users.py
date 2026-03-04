from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.core.security import hash_password, verify_password
from app.core.errors import AppError
from app.core.error_registry import INVALID_CREDENTIALS, EMAIL_EXISTS
from app.models.quota import Quota


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> User:
    """
    Create and persist a new user.

    Raises:
        AppError: if email is already taken
    """
    user = User(
        email=email,
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
    )

    session.add(user)
    try:
        await session.flush()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        raise AppError(EMAIL_EXISTS)
    
    quota = Quota(user_id=user.id)
    session.add(quota)

    return user

async def authenticate_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> User:
    """
    Authenticate a user by email and password.

    Raises:
        AppError
    """
    stmt = select(User).where(User.email==email)
    result = await session.execute(stmt)
    user: User | None = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.hashed_password):
        raise AppError(INVALID_CREDENTIALS)
    return user