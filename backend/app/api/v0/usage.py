from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quota import Quota
from app.schemas.usage import UserQuota
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.core.errors import AppError
from app.core.error_registry import QUOTA_NOT_FOUND

router = APIRouter(prefix="/usage", tags=["usage", "consumption", "quota"])

@router.get("/status", response_model=UserQuota)
async def get_usage(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Quota:
    stmt = select(Quota).where(Quota.user_id == user.id)
    res = await session.execute(stmt)
    quota = res.scalar_one_or_none()
    if quota is None:
        raise AppError(QUOTA_NOT_FOUND)
    
    return quota
