import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.context import request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = str(uuid.uuid4())
        token = request_id.set(rid)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id.reset(token)
