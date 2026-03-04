from typing import List
import re

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    MatchValue, 
    PayloadSchemaType, 
    PointStruct, 
    QueryResponse, 
    VectorParams, 
    Filter, 
    FieldCondition, 
    FilterSelector,
    MatchAny,
)

from app.config import settings
from app.vector_store.base import VectorPoint, VectorStore, VectorFilter


VECTOR_NAME = "text-dense"

class QdrantStore(VectorStore):
    def __init__(
        self,
        *,
        url: str,
        api_key: str,
    ):
        self.client = QdrantClient(
            url=url,
            api_key=api_key,
        )

        self.asyncClient = AsyncQdrantClient(
            url=url,
            api_key=api_key,
        )

    async def create_collection(
        self,
        *,
        name: str,
        vector_size: int,
    ): 
        """
        Creates a qdrant collection in the current cluster.

        Args:
            name (str): the collection name. Must NOT start with a space.
            vector_size (int): An integer specifying the vector dimensions. Make sure this matches the embedding model you will use for points in this collection.

        Returns:
            creation result (bool)
        """
        if await self.asyncClient.collection_exists(name):
            return True

        if not bool(re.match(r'[a-zA-Z][a-zA-Z0-9_-]*$', name.strip())):
            raise Exception("Collection name must be nonempty, start with a letter, and contain only letters, numbers, hyphens, and underscores.")

        return await self.asyncClient.create_collection(
            collection_name=name,
            vectors_config={
                VECTOR_NAME: VectorParams(size=vector_size, distance=Distance.COSINE)
            }
        )

    async def create_indexed_payload_keys(
        self,
        *,
        collection: str,
        keys: List[str],
    ) -> None:
        """
        Indexes paylod keys that can be used for filtering results.

        Args:
            collection (str): the name of the collection to apply indexing to.
            keys (str[]): a list of payload keys to be indexed.

        Returns:
            creation result (bool)
        """
        if not await self.asyncClient.collection_exists(collection):
            raise Exception(f"No collection with the name {collection} exists in the current cluster.")
        for key in keys:
            await self.asyncClient.create_payload_index(
                collection_name=collection,
                field_name=key,
                field_schema=PayloadSchemaType.KEYWORD,
            )

    async def ensure_collection(self, collection_name: str) -> bool:
        return await self.asyncClient.collection_exists(collection_name)

    def upload(self, *, collection: str, points: List[VectorPoint]) -> None:
        qdrant_points = [
            PointStruct(
                id=p.id,
                vector={VECTOR_NAME: p.vector},
                payload=p.payload.to_dict(),
            )
            for p in points
        ]
        self.client.upload_points(
            collection_name=collection,
            points=qdrant_points,
            wait=True,
            batch_size=10,
        )
    
    async def search(
        self, 
        *, 
        collection: str,
        vector: List[float], 
        limit: int = 5, 
        filters: List[VectorFilter] | None = None,
    ) -> QueryResponse:

        if filters is not None:
            must = [FieldCondition(key=f.key, match=MatchAny(any=[v for v in f.values])) for f in filters]
            query_filter = Filter(
                must=must
            )
        else:
            query_filter = None
        return await self.asyncClient.query_points(
            collection_name=collection,
            query=vector,
            using=VECTOR_NAME,
            limit=limit,
            query_filter=query_filter,
        )

    async def get_points_by_page_label(
        self,
        *,
        collection: str,
        page_label: str,
        file_id: str,
    ) -> QueryResponse:
        must = [
            FieldCondition(key="page_label", match=MatchValue(value=page_label)),
            FieldCondition(key="file_id", match=MatchValue(value=file_id))
        ]
        query_filter = Filter(must=must)
        return await self.asyncClient.query_points(
            collection_name=collection,
            using=VECTOR_NAME,
            query_filter=query_filter,
        )

    
    async def count(self, *, collection: str, filters: List[VectorFilter] | None = None):
        if filters is not None:
            must = [FieldCondition(key=f.key, match=MatchAny(any=[v for v in f.values])) for f in filters]
            query_filter = Filter(
                must=must
            )
        else:
            query_filter = None

        return await self.asyncClient.count(collection_name=collection, count_filter=query_filter)

    async def get_points_by_id(self, *, collection: str, ids: List[str]) -> None:
        return await self.asyncClient.retrieve(collection_name=collection, ids=ids)

    def delete_by_filter(
        self, 
        *,
        collection: str,
        filters: List[VectorFilter],
    ) -> None:
        
        must = [FieldCondition(key=f.key, match=MatchAny(any=[v for v in f.values])) for f in filters]
        filter = Filter(
            must=must
        )
        self.client.delete(
            collection_name=collection,
            points_selector=FilterSelector(filter=filter)
        )

    async def adelete_by_filter(
        self, 
        *,
        collection: str,
        filters: List[VectorFilter],
    ) -> None:
        
        must = [FieldCondition(key=f.key, match=MatchAny(any=[v for v in f.values])) for f in filters]
        filter = Filter(
            must=must
        )
        await self.asyncClient.delete(
            collection_name=collection,
            points_selector=FilterSelector(filter=filter)
        )
        
    
qdrant_store = QdrantStore(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)
