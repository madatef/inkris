from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Mapping


@dataclass
class UploadSpec:
    method: str
    url: str
    headers: Mapping[str, str] | None
    fields: Mapping[str, str] | None
    expires_at: str


class StorageProvider(ABC):
    @abstractmethod
    def create_presigned_upload(
        self,
        *,
        file_id,
        size_bytes: int,
        content_type: str | None,
    ) -> UploadSpec:
        ...
    
    @abstractmethod
    def get_object_url(
        self,
        *,
        key: str,
    ) -> str:
        ...