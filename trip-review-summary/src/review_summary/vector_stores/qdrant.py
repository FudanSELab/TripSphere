from typing import Any, Self

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams


class ReviewVectorStore:
    COLLECTION_NAME = "review_embeddings"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    @classmethod
    async def create_repository(
        cls, client: AsyncQdrantClient, vector_dim: int = 3072
    ) -> Self:
        instance = cls(client)
        if not await client.collection_exists(cls.COLLECTION_NAME):
            await client.create_collection(
                collection_name=cls.COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
            )
        return instance

    async def save(self, documents: list[Any]) -> None:
        raise NotImplementedError

    async def find_by_id(self, review_id: str) -> Any | None:
        raise NotImplementedError

    async def delete_by_id(self, review_id: str) -> None:
        raise NotImplementedError

    async def search_by_vector(
        self, embedding_vector: list[float], top_k: int = 10
    ) -> list[Any]:
        raise NotImplementedError
