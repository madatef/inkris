import asyncio
from typing import Optional

import psycopg_pool

from app.config import settings
from app.core.logger import logger

class PostgresPoolManager:
    """
    Owns the single async Postgres connection pool for the process.
    """

    def __init__(self) -> None:
        self._pool: Optional[psycopg_pool.AsyncConnectionPool] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        async with self._lock:
            if self._pool is not None:
                return

            self._pool = psycopg_pool.AsyncConnectionPool(
                conninfo=settings.AGENT_STATE_DATABASE_URL,
                min_size=getattr(settings, "DB_POOL_MIN", 2),
                max_size=getattr(settings, "DB_POOL_MAX", 20),
                timeout=getattr(settings, "DB_POOL_TIMEOUT", 30),
                max_idle=getattr(settings, "DB_POOL_MAX_IDLE", 300),
                open=False,
            )
            await self._pool.open()
            logger.info("Postgres async pool initialized.")

    def get_pool(self) -> psycopg_pool.AsyncConnectionPool:
        if self._pool is None:
            raise RuntimeError("Postgres pool not initialized")
        return self._pool

    async def close(self) -> None:
        async with self._lock:
            if self._pool is not None:
                logger.info("Closing Postgres async pool.")
                await self._pool.close()
                self._pool = None


# Global singleton
_pool_manager = PostgresPoolManager()


async def initialize_pool() -> None:
    await _pool_manager.initialize()


async def close_pool() -> None:
    await _pool_manager.close()


def get_pool() -> psycopg_pool.AsyncConnectionPool:
    return _pool_manager.get_pool()
