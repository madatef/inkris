from contextvars import ContextVar
from uuid import UUID

# Request-scoped unique identifier
request_id: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

user_id: ContextVar[UUID | None] = ContextVar(
    "user_id",
    default=None,
)