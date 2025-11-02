from typing import Any, Literal

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

from chat.config.settings import settings
from chat.infrastructure.mongodb.schema import (
    ConversationDocument,
    ConversationItemDocument,
)
from chat.models import Conversation, ConversationItem
from chat.utils.base64 import decode_page_token, encode_page_token


class MongoConversationRepository:
    def __init__(self, client: AsyncMongoClient[dict[str, Any]]) -> None:
        self.client = client
        self.database = client[settings.mongodb.database]
        self.conversation_collection = self.database["conversation"]
        self.conversation_item_collection = self.database["conversation_item"]

    async def save_conversation(self, conversation: Conversation) -> None:
        document = ConversationDocument.from_model(conversation)
        await self.conversation_collection.replace_one(
            {"_id": document.id}, document.model_dump(), upsert=True
        )

    async def find_conversation(self, conversation_id: str) -> Conversation | None:
        document = await self.conversation_collection.find_one({"_id": conversation_id})
        if document is not None:
            return ConversationDocument.model_validate(document).to_model()
        return None

    async def remove_conversation(self, conversation_id: str) -> int:
        result = await self.conversation_collection.delete_one({"_id": conversation_id})
        return result.deleted_count

    async def list_conversation_items(
        self,
        conversation_id: str,
        page_size: int,
        page_token: str | None,
        direction: Literal["forward", "backward"],
    ) -> tuple[list[ConversationItem], str | None]:
        query: dict[str, Any] = {"conversation_id": conversation_id}
        if last_id := decode_page_token(page_token):
            # When direction is 'backward', we want items with _id < last_id
            query["_id"] = {("$lt" if direction == "backward" else "$gt"): last_id}

        cursor = (
            self.conversation_item_collection.find(query)
            .sort("_id", DESCENDING if direction == "backward" else ASCENDING)
            .limit(limit=page_size)
        )
        documents = await cursor.to_list()

        if not documents:
            return [], None
        conversation_items = [
            ConversationItemDocument.model_validate(document).to_model()
            for document in documents
        ]
        next_page_token = encode_page_token(documents[-1]["_id"])
        return conversation_items, next_page_token
