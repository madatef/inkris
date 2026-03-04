from fastapi import APIRouter, Depends, Request, Response, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.users import (
    create_user,
    authenticate_user,
)
from app.core.auth import create_access_token, issue_refresh_token, revoke_refresh_tokens, refresh_acess_token, get_device_id
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

async def set_token_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.TOKENS_COOKIE_SAMESITE,
        path=settings.TOKENS_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.TOKENS_COOKIE_SAMESITE,
        path=settings.TOKENS_COOKIE_PATH,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

async def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path=settings.TOKENS_COOKIE_PATH,
    )

    response.delete_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        path=settings.TOKENS_COOKIE_PATH,
    )


@router.post("/signup", response_model=UserResponse)
async def signup(
    data: UserCreate,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),  
):

    user = await create_user(
        session,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    response.status_code = status.HTTP_201_CREATED

    access, expiry = create_access_token(subject=str(user.id))
    refresh = await issue_refresh_token(session, user_id=user.id, request=request)
    await set_token_cookies(response, access, refresh)

    await session.commit()
    return user

@router.post("/login", response_model=UserResponse)
async def login(
    data: UserLogin,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(
        session,
        email=data.email,
        password=data.password,
    )

    access, expiry = create_access_token(subject=str(user.id))
    refresh = await issue_refresh_token(session, user_id=user.id, request=request)
    await set_token_cookies(response, access, refresh)
    await session.commit()

    return user

@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user),
):
    return user

@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    rt: str | None = Cookie(default=None, alias=settings.REFRESH_TOKEN_COOKIE_NAME),
):
    access, access_expiry, refresh = await refresh_acess_token(session, refresh_token=rt, request=request)
    await set_token_cookies(response, access, refresh)
    await session.commit()

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):

    device_id = get_device_id(request)
    await revoke_refresh_tokens(session, user_id=user.id, device_id=device_id)
    await session.commit()
    await clear_refresh_cookie(response)
    return
