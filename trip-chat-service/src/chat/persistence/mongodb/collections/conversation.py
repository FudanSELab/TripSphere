from typing import Any

from bson import ObjectId
from pymongo import AsyncMongoClient

from chat.config.settings import settings
from chat.persistence.mongodb.schema import ConversationDocument


class ConversationCollection:
    def __init__(self, client: AsyncMongoClient[dict[str, Any]]) -> None:
        self.client = client
        self.database = client[settings.mongodb.database]
        self.collection = self.database["conversation"]

    async def insert(self, document: ConversationDocument) -> ConversationDocument:
        result = await self.collection.insert_one(
            document.model_dump(by_alias=True, exclude_none=True)
        )
        document.id = str(result.inserted_id)
        return document

    async def find_by_id(self, conversation_id: str) -> ConversationDocument | None:
        document = await self.collection.find_one(
            ObjectId(conversation_id), {"items": 0}
        )
        if document is not None:
            return ConversationDocument.model_validate(document)
        return None

    async def update_metadata(
        self, conversation_id: str, metadata: dict[str, Any]
    ) -> ConversationDocument:
        await self.collection.update_one(
            {"_id": ObjectId(conversation_id)}, {"$set": {"metadata": metadata}}
        )
        document = await self.collection.find_one(ObjectId(conversation_id))
        return ConversationDocument.model_validate(document)

    async def delete_by_id(self, conversation_id: str) -> None:
        await self.collection.delete_one({"_id": ObjectId(conversation_id)})


if __name__ == "__main__":
    ...
