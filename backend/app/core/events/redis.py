from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
from functools import lru_cache
from uuid import uuid4

import redis.asyncio as aioredis
from redis import Redis

from app.config import settings
from app.core.events.types import EventEncoder

CHANNEL = "inkris-events"

@lru_cache(maxsize=1)
def get_async_redis():
    return aioredis.Redis.from_url(
        url=settings.EVENTS_BROKER_URL,
        decode_responses=True,
        max_connections=10,
    )

@lru_cache(maxsize=1)
def get_redis():
    return Redis.from_url(
        url=settings.EVENTS_BROKER_URL,
        decode_responses=True,
        max_connections=10,
    )

def publish(event: any):
    if not is_dataclass(event):
        raise ValueError("Events must be dataclasses")

    payload = {
        "type": event.__class__.__name__,
        "data": asdict(event),
        "event_id": str(uuid4()),
        "published_at": datetime.now(timezone.utc).isoformat()
    }
    r = get_redis()
    r.publish(CHANNEL, json.dumps(payload, cls=EventEncoder))
