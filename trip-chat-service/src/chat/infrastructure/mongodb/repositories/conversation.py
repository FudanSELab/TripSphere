from typing import Any, Literal

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

from chat.config.settings import settings
from chat.infrastructure.mongodb.schema import (
    ConversationDocument,
    ConversationItemDocument,
)
from chat.models import Conversation, ConversationItem
from chat.utils.base64 import decode_page_token, encode_page_token


class ConversationRepository:
    def __init__(self, client: AsyncMongoClient[dict[str, Any]]) -> None:
        self.client = client
        self.database = client[settings.mongodb.database]
        self.collection = self.database["conversation"]

    async def save(self, conversation: Conversation) -> None:
        document = ConversationDocument.from_model(conversation)
        await self.collection.replace_one(
            {"_id": document.id}, document.model_dump(), upsert=True
        )

    async def find_by_id(self, conversation_id: str) -> Conversation | None:
        document = await self.collection.find_one({"_id": conversation_id})
        if document is not None:
            return ConversationDocument.model_validate(document).to_model()
        return None

    async def remove_by_id(self, conversation_id: str) -> int:
        result = await self.collection.delete_one({"_id": conversation_id})
        return result.deleted_count


class ConversationItemRepository:
    def __init__(self, client: AsyncMongoClient[dict[str, Any]]) -> None:
        self.client = client
        self.database = client[settings.mongodb.database]
        self.collection = self.database["conversation_item"]

    async def save(self, conversation_item: ConversationItem) -> None:
        document = ConversationItemDocument.from_model(conversation_item)
        await self.collection.replace_one(
            {"_id": document.id}, document.model_dump(), upsert=True
        )

    async def find_by_id(self, item_id: str) -> ConversationItem | None:
        document = await self.collection.find_one({"_id": item_id})
        if document is not None:
            return ConversationItemDocument.model_validate(document).to_model()
        return None

    async def remove_by_conversation_id(self, conversation_id: str) -> int:
        result = await self.collection.delete_many({"conversation_id": conversation_id})
        return result.deleted_count

    async def find_all_by_conversation_id(
        self,
        conversation_id: str,
        page_size: int,
        page_token: str | None,
        order: Literal["asc", "desc"],
    ) -> tuple[list[ConversationItem], int, str | None]:
        query: dict[str, Any] = {"conversation_id": conversation_id}
        if last_id := decode_page_token(page_token):
            # When order is 'desc', we want items with _id < last_id
            query["_id"] = {("$lt" if order == "desc" else "$gt"): last_id}

        cursor = (
            self.collection.find(query)
            .sort("_id", DESCENDING if order == "desc" else ASCENDING)
            .limit(limit=page_size)
        )

        documents = await cursor.to_list()
        total = await self.collection.count_documents(
            {"conversation_id": conversation_id}
        )
        if not documents:
            return [], total, None

        conversation_items = [
            ConversationItemDocument.model_validate(document).to_model()
            for document in documents
        ]
        next_page_token = encode_page_token(documents[-1]["_id"])

        return conversation_items, total, next_page_token
