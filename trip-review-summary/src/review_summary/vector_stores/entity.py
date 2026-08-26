import logging
from typing import Any, Self

from qdrant_client import AsyncQdrantClient, models

from review_summary.models import Entity

logger = logging.getLogger(__name__)


class EntityVectorStore:
    COLLECTION_NAME = "review_summary_entities"

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

        if not points:
            return
        result = await self.client.upsert(self.COLLECTION_NAME, points=points)
        logger.debug(f"Qdrant upsert result: {result}")

    async def delete_by_target(self, target_id: str, target_type: str) -> None:
        await self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=_target_filter(target_id, target_type)
            ),
            wait=True,
        )

    async def find_by_target(
        self,
        target_id: str,
        target_type: str,
    ) -> list[Entity]:
        target_filter = _target_filter(target_id, target_type)
        offset: Any = None
        seen_offsets: set[str] = set()
        entities: list[Entity] = []

        while True:
            records, next_offset = await self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                scroll_filter=target_filter,
                limit=256,
                offset=offset,
            )
            entities.extend(
                Entity.model_validate({"id": record.id, **(record.payload or {})})
                for record in records
            )
            if next_offset is None:
                return entities

            offset_key = repr(next_offset)
            if next_offset == offset or offset_key in seen_offsets:
                raise RuntimeError("Qdrant returned a repeated scroll offset")
            seen_offsets.add(offset_key)
            offset = next_offset

    async def search_by_vector(
        self,
        embedding_vector: list[float],
        target_id: str,
        target_type: str,
        review_snapshot: str | None = None,
        top_k: int = 10,
        vector_name: str = "description",  # Add parameter to specify which vector
    ) -> list[Entity]:
        response = await self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=embedding_vector,
            using=vector_name,  # Specify which named vector to use
            query_filter=_target_filter(target_id, target_type, review_snapshot),
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


def _target_filter(
    target_id: str,
    target_type: str,
    review_snapshot: str | None = None,
) -> models.Filter:
    conditions = [
        models.FieldCondition(
            key="attributes.target_id",
            match=models.MatchValue(value=target_id),
        ),
        models.FieldCondition(
            key="attributes.target_type",
            match=models.MatchValue(value=target_type),
        ),
    ]
    if review_snapshot is not None:
        conditions.append(
            models.FieldCondition(
                key="attributes.review_snapshot",
                match=models.MatchValue(value=review_snapshot),
            )
        )
    return models.Filter(must=conditions)
