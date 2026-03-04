from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL)
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
)

agent_db_engine = create_async_engine(settings.AGENT_STATE_DATABASE_URL_ASYNC)
AgentDBSessionLocal = async_sessionmaker(agent_db_engine)