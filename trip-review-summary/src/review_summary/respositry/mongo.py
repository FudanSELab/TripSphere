from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

class ReviewEmbedding(BaseModel):
    """
    Review embedding document model
    
    Include:
    - embedding_id: Mongodb ObjectId
    - attraction_id: Attraction ID
    - review_id: Review ID
    - embedding: List of float numbers representing the embedding vector
    - review_content: The content of the review
    """
    
    embedding_id: ObjectId = Field(default=None,alias="_id")
    attraction_id: str = Field(..., description="attraction ID")
    review_id: str = Field(..., description="review ID")
    embedding: List[float] = Field(..., description="embedding vector")
    review_content:str = Field(..., description="review content")
    class Config:
        avalidate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ReviewEmbeddingRepository:
    """Attraction Embedding Repository for MongoDB operations."""
    
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str = "review_embeddings"):
        self.collection: AsyncIOMotorCollection = database[collection_name]

    async def create_embedding(self, review_id:str, attraction_id: str, embedding: List[float], review_content: str) -> str:
        """Create a new attraction embedding record and return id(not attraction_id)."""
        embedding_doc = ReviewEmbedding(
            attraction_id=attraction_id,
            review_id=review_id,
            embedding=embedding,
            review_content=review_content
        )
        embedding_dict = embedding_doc.model_dump(by_alias=True, exclude_unset=True,exclude={"embedding_id"})
        result = await self.collection.insert_one(document=embedding_dict)
        return str(result.inserted_id)

    async def find_by_id(self, embedding_id: str) -> Optional[ReviewEmbedding]:
        """Find embedding by its MongoDB ObjectId"""
        embedding_data = await self.collection.find_one({"_id": ObjectId(embedding_id)})
        if embedding_data:
            return ReviewEmbedding(**embedding_data)
        return None

    async def find_by_review_id(self, review_id: str) -> Optional[ReviewEmbedding]:
        """Find embedding by review id"""
        embedding_data = await self.collection.find_one({"review_id": review_id})
        if embedding_data:
            return ReviewEmbedding(**embedding_data)
        return None

    async def update_embedding(self, embedding_id: str, review_content: str,
                              embedding: Optional[List[float]] = None) -> bool:
        """update embedding record by its MongoDB ObjectId"""
        update_data = {}
        if embedding is not None:
            update_data["embedding"] = embedding
        if review_content is not None:
            update_data["review_content"] = review_content

        result = await self.collection.update_one(
            {"_id": ObjectId(embedding_id)}, 
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return True
        return False

    async def update_embedding_by_review_id(
        self,
        review_id: str,
        embedding: List[float],
        review_content: str
    ) ->bool:
        """update embedding by attraction_id"""
        embedding_record = await self.find_by_review_id(review_id)
        if not embedding_record:
            return False
        
        return await self.update_embedding(
            embedding_id=str(embedding_record.embedding_id),
            embedding=embedding,
            review_content=review_content
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

    async def find_by_attraction_id(self, attraction_id: str) -> List[ReviewEmbedding]:
        """Find embeddings by attraction id"""
        embeddings = []
        cursor = self.collection.find({"attraction_id": attraction_id})
        async for embedding_data in cursor:
            embeddings.append(ReviewEmbedding(**embedding_data))
        return embeddings
