import base64
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

from chat.config.settings import settings
from chat.storage.mongodb.schema import (
    ConversationItemDocument,
    ConversationItemKind,
    MessageDocument,
    TaskDocument,
)


class ConversationItemCollection:
    def __init__(self, client: AsyncMongoClient[dict[str, Any]]) -> None:
        self.client = client
        self.database = client[settings.mongodb.database]
        self.collection = self.database["conversation_item"]

    async def insert(
        self, document: ConversationItemDocument
    ) -> ConversationItemDocument:
        result = await self.collection.insert_one(
            document.model_dump(by_alias=True, exclude_none=True)
        )
        document.id = result.inserted_id
        return document

    @staticmethod
    def encode_token(oid: ObjectId | None) -> str | None:
        if oid is None:
            return None
        return base64.urlsafe_b64encode(oid.binary).decode("utf-8")

    @staticmethod
    def decode_token(token: str | None) -> ObjectId | None:
        if token is None:
            return None
        binary = base64.urlsafe_b64decode(token.encode("utf-8"))
        return ObjectId(binary)

    async def list_by_conversation(
        self, conversation_id: str, page_size: int, page_token: str | None, order: str
    ) -> tuple[list[TaskDocument | MessageDocument], int, str | None]:
        query: dict[str, Any] = {"conversation_id": conversation_id}
        if last_id := self.decode_token(page_token) is not None:
            # When order is 'desc', we want items with _id < last_id
            query["_id"] = {"$lt" if order == "desc" else "$gt": last_id}

        cursor = (
            self.collection.find(query)
            .sort("_id", DESCENDING if order == "desc" else ASCENDING)
            .limit(limit=page_size)
        )

        documents = await cursor.to_list(length=None)
        total = await self.collection.count_documents(
            {"conversation_id": conversation_id}
        )
        if not documents:
            return [], total, None

        def _from_dict(document: dict[str, Any]) -> TaskDocument | MessageDocument:
            if document["kind"] == ConversationItemKind.TASK:
                return TaskDocument.model_validate(document)
            elif document["kind"] == ConversationItemKind.MESSAGE:
                return MessageDocument.model_validate(document)
            else:
                raise ValueError(f"Unknown ConversationItemKind: {document['kind']}")

        conversation_items = [_from_dict(document) for document in documents]
        next_page_token = self.encode_token(documents[-1]["_id"])

        return conversation_items, total, next_page_token


if __name__ == "__main__":
    ...
