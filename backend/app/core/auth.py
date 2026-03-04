from datetime import timedelta, timezone, datetime
import secrets
from uuid import UUID

from jose import jwt, JWTError
import hmac
import hashlib
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from app.config import settings
from app.core.error_registry import INVALID_TOKEN
from app.core.errors import AppError
from app.models.refresh_token import RefreshToken


def _now() -> datetime:
    return datetime.now(timezone.utc)

# -------------
# Access tokens
# -------------

def create_access_token(
    *,
    subject: str,
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """
    Create a signed JWT access token.
    Returns (token, expiry)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = _now() + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return token, expire.isoformat()

def decode_access_token(token: str) -> str:
    """
    Validate and decode JWT access token
    Returns: the subject of the token (user identifier in our case)
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise AppError(INVALID_TOKEN)
    subject = payload.get("sub")
    if subject is None:
        raise AppError(INVALID_TOKEN)

    return subject

# --------------
# Refresh tokens
# --------------

def get_device_id(request: Request) -> str:
    """Creates a stable ID for the client device.
    Used to manage refresh tokens per device.
    """
    user_agent = request.headers.get("user-agent", "")

    client_ip = request.client.host
    if forwarded := request.headers.get("x-forwarded-for"):
        client_ip = forwarded.split(",")[0].strip()
    elif real_ip := request.headers.get("x-real-ip"):
        client_ip = real_ip

    id_string = f"{user_agent}|{client_ip}"
    id = hashlib.sha256(id_string.encode()).hexdigest()

    return id

async def revoke_refresh_tokens(
    session: AsyncSession,
    *,
    user_id: UUID,
    device_id: str,
) -> bool:
    """
    Revokes a refresh token (best-effort).
    Returns True if a token was revoked, False otherwise.
    """
    now = _now()
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.device_id == device_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .values(revoked_at=now, last_used_at=now)
    )
    res = await session.execute(stmt)
    await session.flush()
    return (res.rowcount or 0) > 0

async def issue_refresh_token(
    session: AsyncSession,
    *,
    user_id: UUID,
    request: Request,
) -> str:
    """
    Creates a new refresh token row, returns the *raw* token value (only time you see it) and
    revokes any existing tokens for the same user-device-browser combination.
    """
    device_id = get_device_id(request)
    await revoke_refresh_tokens(session, user_id=user_id, device_id=device_id)

    raw = secrets.token_urlsafe(64)
    key = settings.SECRET_KEY.encode("utf-8")
    msg = raw.encode("utf-8") 
    token_hash = hmac.new(key, msg, hashlib.sha256).hexdigest()

    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        device_id=device_id,
        expires_at=_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(rt)
    await session.flush()
    return raw

async def refresh_acess_token(
    session: AsyncSession,
    *,
    refresh_token: str | None,
    request: Request,
) -> tuple[str, str, str]:
    """Creates a new acess token using an active refresh token.
    \nRefresh token is then revoked and a new one is issued (token rotation).
    \nReturns a tuple (access_token, refresh_token).
    """
    if refresh_token is None:
        raise AppError(INVALID_TOKEN)
    now = _now()
    key = settings.SECRET_KEY.encode("utf-8")
    msg = refresh_token.encode("utf-8")
    token_hash = hmac.new(key, msg, hashlib.sha256).hexdigest()
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    res = await session.execute(stmt)
    rt = res.scalar_one_or_none()
    if rt is None or rt.expires_at < now:
        raise AppError(INVALID_TOKEN)

    user_id = rt.user_id
    new_rt = await issue_refresh_token(session, user_id=user_id, request=request)
    access_token, expiry = create_access_token(subject=str(user_id))
    return access_token, expiry, new_rt
