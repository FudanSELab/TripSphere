import asyncio
import logging
from typing import Any, Self

import pandas as pd
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
            # Remove id (UUID) from payload
            text_unit_id = payload.pop("id")
            # Remove embedding from payload
            embedding: list[float] | None = payload.pop("embedding")
            if embedding is None:
                logger.warning(
                    f"Skip TextUnit {text_unit_id} due to missing embedding."
                )
                continue
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
            TextUnit.model_validate({"id": record.id, **(record.payload or {})})
            for record in records
        ]
        return text_units

    async def search_by_vector(
        self, embedding_vector: list[float], top_k: int = 10
    ) -> list[TextUnit]:
        raise NotImplementedError

    async def update_final_text_units(
        self, text_units: list[TextUnit] | pd.DataFrame
    ) -> None:
        """Update final text units (already embedded) in the vector store."""
        points_payloads: list[tuple[str, dict[str, Any]]] = []
        if isinstance(text_units, pd.DataFrame):
            selected = text_units.loc[:, ["id", "entity_ids", "relationship_ids"]]
            for row in selected.itertuples():
                text_unit_id = str(row.id)
                points_payloads.append(
                    (
                        text_unit_id,
                        {
                            "entity_ids": row.entity_ids,
                            "relationship_ids": row.relationship_ids,
                        },
                    )
                )
        else:
            for text_unit in text_units:
                text_unit_id = text_unit.id
                points_payloads.append(
                    (
                        text_unit_id,
                        {
                            "entity_ids": text_unit.entity_ids,
                            "relationship_ids": text_unit.relationship_ids,
                        },
                    )
                )

        # Concurrently update payloads
        tasks = [
            asyncio.create_task(
                self.client.set_payload(
                    collection_name=self.COLLECTION_NAME,
                    payload=payload,
                    points=[text_unit_id],
                )
            )
            for text_unit_id, payload in points_payloads
        ]
        if len(tasks) > 0:
            await asyncio.wait(tasks)
