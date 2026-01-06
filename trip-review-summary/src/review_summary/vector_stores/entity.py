import logging
from typing import Self

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from review_summary.models import Entity

logger = logging.getLogger(__name__)


class EntityVectorStore:
    COLLECTION_NAME = "review_summary_entity_embeddings"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    @classmethod
    async def create_vector_store(
        cls, client: AsyncQdrantClient, vector_dim: int = 3072
    ) -> Self:
        if (await client.collection_exists(cls.COLLECTION_NAME)) is False:
            await client.create_collection(
                collection_name=cls.COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
            )
        return cls(client)

    async def search_by_vector(
        self, embedding_vector: list[float], top_k: int = 10
    ) -> list[Entity]:
        raise NotImplementedError
