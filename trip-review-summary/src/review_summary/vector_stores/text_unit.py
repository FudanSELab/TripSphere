import logging
from typing import Self

from qdrant_client import AsyncQdrantClient, models

from review_summary.models import TextUnit

logger = logging.getLogger(__name__)


class TextUnitVectorStore:
    COLLECTION_NAME = "review_summary_text_unit_embeddings"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    @classmethod
    async def create_vector_store(
        cls, client: AsyncQdrantClient, vector_dim: int = 3072
    ) -> Self:
        if (await client.collection_exists(cls.COLLECTION_NAME)) is False:
            await client.create_collection(
                collection_name=cls.COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=vector_dim, distance=models.Distance.COSINE
                ),
            )
        return cls(client)

    async def save_multiple(self, text_units: list[TextUnit]) -> None:
        if len(text_units) == 0:
            return  # No items to save

        points: list[models.PointStruct] = []
        for text_unit in text_units:
            payload = text_unit.model_dump()
            text_unit_id = payload.pop("id")  # Remove id from payload
            embedding = payload.pop("embedding")  # Remove embedding from payload
            point = models.PointStruct(
                id=text_unit_id, vector=embedding, payload=payload
            )
            points.append(point)

        result = await self.client.upsert(self.COLLECTION_NAME, points=points)
        logger.debug(f"Qdrant upsert result: {result}")

    async def find_by_target(
        self, target_id: str, target_type: str, limit: int = 1024
    ) -> list[TextUnit]:
        """Find text units (without embedding) by target ID and target type."""
        filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="attributes.target_id",
                    match=models.MatchValue(value=target_id),
                ),
                models.FieldCondition(
                    key="attributes.target_type",
                    match=models.MatchValue(value=target_type),
                ),
            ]
        )
        records, _ = await self.client.scroll(
            collection_name=self.COLLECTION_NAME, scroll_filter=filter, limit=limit
        )
        text_units: list[TextUnit] = [
            TextUnit.model_validate(record.payload or {}) for record in records
        ]
        return text_units

    async def search_by_vector(
        self, embedding_vector: list[float], top_k: int = 10
    ) -> list[TextUnit]:
        raise NotImplementedError
