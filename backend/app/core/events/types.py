from dataclasses import dataclass
from uuid import UUID
from typing import Optional
from datetime import datetime
import json


@dataclass(slots=True)
class FileProcessingEvent:
    file_id: UUID
    user_id: UUID
    status: str   # processing | ready | error
    progress: int # percentage from 1 to 100
    error: Optional[str] = None

class EventEncoder(json.JSONEncoder):
    """Converts json-unserializable objects in the event instance to strings."""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)