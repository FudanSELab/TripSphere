import logging
from typing import Any, Self

from qdrant_client import AsyncQdrantClient, models

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
                vectors_config={
                    "description": models.VectorParams(
                        size=vector_dim, distance=models.Distance.COSINE
                    ),
                    "title": models.VectorParams(
                        size=vector_dim, distance=models.Distance.COSINE
                    ),
                },
            )
        return cls(client)

    async def save_multiple(self, entities: list[Entity]) -> None:
        if len(entities) == 0:
            return  # No items to save

        points: list[models.PointStruct] = []
        for entity in entities:
            payload = entity.model_dump()
            # Remove id (UUID) from payload
            entity_id = payload.pop("id")
            # Remove embeddings from payload
            vector: dict[str, Any] = {}
            if description_embedding := payload.pop("description_embedding", None):
                vector["description"] = description_embedding
            if title_embedding := payload.pop("title_embedding", None):
                vector["title"] = title_embedding
            if not vector:
                logger.warning(f"Skip Entity {entity_id} due to missing embedding.")
                continue

            point = models.PointStruct(id=entity_id, vector=vector, payload=payload)
            points.append(point)

        result = await self.client.upsert(self.COLLECTION_NAME, points=points)
        logger.debug(f"Qdrant upsert result: {result}")

    async def search_by_vector(
        self,
        embedding_vector: list[float],
        target_id: str,
        target_type: str = "attraction",
        top_k: int = 10,
        vector_name: str = "description",  # Add parameter to specify which vector
    ) -> list[Entity]:
        response = await self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=embedding_vector,
            using=vector_name,  # Specify which named vector to use
            query_filter=models.Filter(
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
            ),
            limit=top_k,
        )
        # Convert response to list of Entity
        entities: list[Entity] = [
            Entity.model_validate(
                {
                    "id": point.id,
                    "rank": int(point.score * 100),
                    **(point.payload or {}),
                }
            )
            for point in response.points
        ]
        return entities
