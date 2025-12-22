from typing import Any

from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo.asynchronous.collection import AsyncCollection


class ReviewEmbedding(BaseModel):
    """Review embedding document model"""

    embedding_id: ObjectId | None = Field(default=None, alias="_id")
    attraction_id: str = Field(..., description="Attraction ID")
    review_id: str = Field(..., description="Review ID")
    embedding: list[float] = Field(..., description="Embedding vector")
    review_content: str = Field(..., description="Review content")

    class Config:  # TODO: Migrate to V2
        avalidate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ReviewEmbeddingRepository:
    """Attraction Embedding Repository for MongoDB operations."""

    COLLECTION_NAME = "review_embeddings"

    def __init__(self, collection: AsyncCollection[dict[str, Any]]):
        self.collection = collection

    async def create_embedding(
        self,
        review_id: str,
        attraction_id: str,
        embedding: list[float],
        review_content: str,
    ) -> str:
        """Create a new attraction embedding record and return id(not attraction_id)."""
        embedding_doc = ReviewEmbedding(
            attraction_id=attraction_id,
            review_id=review_id,
            embedding=embedding,
            review_content=review_content,
        )
        embedding_dict = embedding_doc.model_dump(
            by_alias=True, exclude_unset=True, exclude={"embedding_id"}
        )
        result = await self.collection.insert_one(document=embedding_dict)
        return str(result.inserted_id)

    async def find_by_id(self, embedding_id: str) -> ReviewEmbedding | None:
        """Find embedding by its MongoDB ObjectId"""
        embedding_data = await self.collection.find_one({"_id": ObjectId(embedding_id)})
        if embedding_data:
            return ReviewEmbedding(**embedding_data)
        return None

    async def find_by_review_id(self, review_id: str) -> ReviewEmbedding | None:
        """Find embedding by review id"""
        embedding_data = await self.collection.find_one({"review_id": review_id})
        if embedding_data:
            return ReviewEmbedding(**embedding_data)
        return None

    async def update_embedding(
        self,
        embedding_id: str,
        review_content: str,
        embedding: list[float] | None = None,
    ) -> bool:
        """update embedding record by its MongoDB ObjectId"""
        update_data = {}
        if embedding is not None:
            update_data["embedding"] = embedding
        update_data["review_content"] = review_content

        result = await self.collection.update_one(
            {"_id": ObjectId(embedding_id)}, {"$set": update_data}
        )

        if result.modified_count > 0:
            return True
        return False

    async def update_embedding_by_review_id(
        self, review_id: str, embedding: list[float], review_content: str
    ) -> bool:
        """update embedding by attraction_id"""
        embedding_record = await self.find_by_review_id(review_id)
        if not embedding_record:
            return False

        return await self.update_embedding(
            embedding_id=str(embedding_record.embedding_id),
            embedding=embedding,
            review_content=review_content,
        )

    async def delete_embedding(self, embedding_id: str) -> bool:
        """delete embedding by its MongoDB ObjectId"""
        result = await self.collection.delete_one({"_id": ObjectId(embedding_id)})
        return result.deleted_count > 0

    async def delete_embedding_by_review_id(self, review_id: str) -> bool:
        """delete embedding by its attraction_id"""
        embedding_record = await self.find_by_review_id(review_id)
        if not embedding_record:
            return False

        result = await self.delete_embedding(str(embedding_record.embedding_id))
        return result

    async def find_by_attraction_id(self, attraction_id: str) -> list[ReviewEmbedding]:
        """Find embeddings by attraction id"""
        embeddings: list[ReviewEmbedding] = []
        cursor = self.collection.find({"attraction_id": attraction_id})
        async for embedding_data in cursor:
            embeddings.append(ReviewEmbedding(**embedding_data))
        return embeddings
