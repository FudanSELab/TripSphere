import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)


class ReviewVectorStore:
    """Store items and their embeddings in Qdrant."""

    COLLECTION_NAME = "review_embeddings"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def save(self, items: list[PointStruct]) -> None:
        if len(items) == 0:
            return  # No items to save
        result = await self.client.upsert(self.COLLECTION_NAME, points=items)
        logger.debug(f"Qdrant upsert result: {result}")

    async def find_by_id(self, item_id: str) -> Any | None:
        raise NotImplementedError

    async def delete_by_id(self, item_id: str) -> None:
        raise NotImplementedError

    async def search_by_vector(
        self, embedding_vector: list[float], top_k: int = 10
    ) -> list[Any]:
        raise NotImplementedError
