import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user
from app.core.events.redis import get_async_redis, CHANNEL

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/stream")
async def event_stream(user=Depends(get_current_user)):
    r = get_async_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)

    async def generator():
        try:
            async for msg in pubsub.listen():
                if msg["type"] != "message":
                    continue

                event = json.loads(msg["data"])

                # Strict user isolation
                if event["data"].get("user_id") != str(user.id):
                    continue

                yield f"event: {event['type']}\n"
                yield f"data: {json.dumps(event['data'])}\n\n"

        finally:
            await pubsub.unsubscribe(CHANNEL)
            await pubsub.close()

    return StreamingResponse(
        generator(), 
        media_type="text/event-stream", 
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
