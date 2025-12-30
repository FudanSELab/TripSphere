import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

from review_summary.models import TextUnit

logger = logging.getLogger(__name__)


class TextUnitVectorStore:
    COLLECTION_NAME = "text_unit_embeddings"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def save_multiple(self, text_units: list[TextUnit]) -> None:
        if len(text_units) == 0:
            return  # No items to save

        points: list[PointStruct] = []
        for text_unit in text_units:
            payload = text_unit.model_dump()
            tu_id = payload.pop("id")  # Remove id from payload
            embedding = payload.pop("embedding")  # Remove embedding from payload
            point = PointStruct(id=tu_id, vector=embedding, payload=payload)
            points.append(point)

        result = await self.client.upsert(self.COLLECTION_NAME, points=points)
        logger.debug(f"Qdrant upsert result: {result}")

    async def find_by_id(self, text_unit_id: str) -> Any | None:
        raise NotImplementedError

    async def delete_by_id(self, text_unit_id: str) -> None:
        raise NotImplementedError

    async def search_by_vector(
        self, embedding_vector: list[float], top_k: int = 10
    ) -> list[TextUnit]:
        raise NotImplementedError
