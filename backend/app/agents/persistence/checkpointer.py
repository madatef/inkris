import asyncio
from typing import Optional

import psycopg
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings
from app.agents.persistence.pool import get_pool
from app.core.logger import logger


class CheckpointerManager:
    """
    LangGraph checkpointer backed by the shared Postgres pool.
    """

    def __init__(self) -> None:
        self._saver: Optional[AsyncPostgresSaver] = None
        self._setup_complete = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        async with self._lock:
            if self._saver is not None:
                return

            # One-time schema setup using autocommit connection
            if not self._setup_complete:
                conn = await psycopg.AsyncConnection.connect(
                    settings.AGENT_STATE_DATABASE_URL,
                    autocommit=True,
                    connect_timeout=10,
                    # Keep connection alive during setup
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5
                )
                try:
                    logger.info("Running LangGraph checkpointer setup.")
                    await AsyncPostgresSaver(conn).setup()
                    self._setup_complete = True
                finally:
                    await conn.close()

            pool = get_pool()
            self._saver = AsyncPostgresSaver(pool)
            logger.info("LangGraph checkpointer initialized.")

    def get_saver(self) -> AsyncPostgresSaver:
        if self._saver is None:
            raise RuntimeError("Checkpointer not initialized")
        return self._saver


# Global singleton
_checkpointer = CheckpointerManager()


async def initialize_checkpointer() -> None:
    await _checkpointer.initialize()


def get_checkpointer() -> AsyncPostgresSaver:
    return _checkpointer.get_saver()
