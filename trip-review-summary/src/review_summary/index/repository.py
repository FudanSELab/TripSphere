from typing import Any, Self

from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointIdsList,
    PointStruct,
    Record,
    ScoredPoint,
    VectorParams,
)

from review_summary.utils.uuid import uuid7


class ReviewEmbedding(BaseModel):
    review_id: str = Field(
        alias="_id",
        default_factory=lambda: str(uuid7()),
        description="Unique identifier of the Review.",
    )
    target_id: str = Field(..., description="Target ID")
    embedding: list[float] = Field(..., description="Embedding vector")
    content: str = Field(..., description="Review content")
    metadata: dict[str, Any] | None = Field(default=None)


class ReviewEmbeddingRepository:
    COLLECTION_NAME = "review_embeddings"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    @classmethod
    async def create_repository(cls, client: AsyncQdrantClient) -> Self:
        instance = cls(client)
        if not await client.collection_exists(cls.COLLECTION_NAME):
            await client.create_collection(
                collection_name=cls.COLLECTION_NAME,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
            )
        return instance

    def _convert_to_point(self, embedding: ReviewEmbedding) -> PointStruct:
        payload = embedding.model_dump()
        payload.pop("embedding")
        payload.pop("review_id")
        return PointStruct(
            id=embedding.review_id,
            vector=embedding.embedding,
            payload=payload,
        )

    def _convert_from_record(self, record: Record) -> ReviewEmbedding:
        payload = record.payload if record.payload else {}
        payload["review_id"] = record.id
        payload["embedding"] = record.vector
        return ReviewEmbedding.model_validate(payload)

    def _convert_from_scored_point(self, scored_point: ScoredPoint) -> ReviewEmbedding:
        payload = scored_point.payload if scored_point.payload else {}
        payload["review_id"] = scored_point.id
        payload["embedding"] = scored_point.vector
        review_embedding = ReviewEmbedding.model_validate(payload)
        review_embedding.metadata = {"score": scored_point.score}
        return review_embedding

    async def save(self, embedding: ReviewEmbedding) -> None:
        point = self._convert_to_point(embedding)
        await self.client.upsert(collection_name=self.COLLECTION_NAME, points=[point])

    async def find_by_id(self, document_id: str) -> ReviewEmbedding | None:
        result = await self.client.retrieve(
            collection_name=self.COLLECTION_NAME, ids=[document_id]
        )
        if len(result) > 0:
            return self._convert_from_record(result[0])
        return None

    async def delete_by_id(self, document_id: str) -> None:
        await self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=PointIdsList(points=[document_id]),
        )

    async def query_by_vector(
        self, embedding_vector: list[float], top_k: int = 10
    ) -> list[ReviewEmbedding]:
        response = await self.client.query_points(
            collection_name=self.COLLECTION_NAME, query=embedding_vector, limit=top_k
        )
        return [self._convert_from_scored_point(point) for point in response.points]

    async def update_embedding_review(
        self, review_id: str, embedding: list[float], review_content: str
    ) -> None: ...
