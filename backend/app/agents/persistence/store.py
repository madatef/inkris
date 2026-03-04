import asyncio
from typing import Optional

from psycopg_pool import AsyncConnectionPool

from app.agents.persistence.pool import get_pool
from app.core.logger import logger


class AgentStore:
    """
    Application-level key/value store sharing the Postgres pool.
    """

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool
        self._setup_complete = False
        self._lock = asyncio.Lock()

    async def setup(self) -> None:
        async with self._lock:
            if self._setup_complete:
                return

            logger.info("Setting up AgentStore schema.")
            async with self._pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS agent_store (
                            id TEXT PRIMARY KEY,
                            data JSONB NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        );
                        """
                    )

            self._setup_complete = True
            logger.info("AgentStore setup complete.")

    async def get(self, id: str) -> Optional[dict]:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT data FROM agent_store WHERE id = %s;",
                    (id,),
                )
                row = await cur.fetchone()
                return row[0] if row else None

    async def upsert(self, id: str, data: dict) -> None:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO agent_store (id, data)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET data = EXCLUDED.data,
                        updated_at = now();
                    """,
                    (id, data),
                )


# Global singleton
_store: AgentStore | None = None


async def initialize_store() -> None:
    global _store
    pool = get_pool()
    _store = AgentStore(pool)
    await _store.setup()


def get_store() -> AgentStore:
    if _store is None:
        raise RuntimeError("Store not initialized")
    return _store
