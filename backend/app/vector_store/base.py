from abc import ABC, abstractmethod
from typing import Sequence, List
from dataclasses import asdict, dataclass
from uuid import UUID

from app.core.enums import ChunkTypeEnum


@dataclass(frozen=True, kw_only=True)
class VectorPayload:
    user_id: UUID
    file_id: UUID
    page_label: int
    parent_id: str | None
    start_char_idx: int
    end_char_idx: int
    prev_point_id: str | None
    next_point_id: str | None
    text: str | None
    chunk_type: ChunkTypeEnum

    def to_dict(self) -> dict:
        return asdict(self)

class VectorPoint:
    def __init__(
        self,
        *,
        id: str,
        vector: list[float],
        payload: VectorPayload,
    ):
        self.id = id
        self.vector = vector
        self.payload = payload

class VectorFilter:
    def __init__(
        self,
        *,
        key: str,
        values: list[str],
    ):
        self.key = key
        self.values = values

class VectorStore(ABC):
    @abstractmethod
    def ensure_collection(self, collection_name: str) -> None:
        ...

    @abstractmethod
    def upload(self, points: Sequence[VectorPoint], collection: str) -> None:
        ...

    @abstractmethod
    def search(
        self,
        *,
        vector: list[float],
        limit: int,
        filters: dict | None = None,
        collection: str,
    ):
        ...
    
    @abstractmethod
    def get_points_by_id(self, ids: List[str], collection: str) -> None:
        ...
    
    @abstractmethod
    def delete_by_filter(self, filters: dict, collection: str) -> None:
        ...
