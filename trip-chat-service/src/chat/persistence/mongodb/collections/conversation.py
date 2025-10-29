from typing import Any, Literal

from bson import ObjectId
from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

from chat.config.settings import settings
from chat.persistence.mongodb.schema import (
    ConversationDocument,
    ConversationItemDocument,
    ConversationItemKind,
    MessageDocument,
    TaskDocument,
)
from chat.utils.base64 import decode_page_token, encode_page_token


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
        document = await self.collection.find_one(ObjectId(conversation_id))
        if document is not None:
            return ConversationDocument.model_validate(document)
        return None

    async def update_metadata(
        self, conversation_id: str, metadata: dict[str, Any]
    ) -> ConversationDocument | None:
        result = await self.collection.update_one(
            {"_id": ObjectId(conversation_id)}, {"$set": {"metadata": metadata}}
        )
        if result.matched_count == 0:
            return None
        document = await self.collection.find_one(ObjectId(conversation_id))
        return ConversationDocument.model_validate(document)

    async def delete_by_id(self, conversation_id: str) -> int:
        result = await self.collection.delete_one({"_id": ObjectId(conversation_id)})
        return result.deleted_count


class ConversationItemCollection:
    def __init__(self, client: AsyncMongoClient[dict[str, Any]]) -> None:
        self.client = client
        self.database = client[settings.mongodb.database]
        standard_opts: CodecOptions[dict[str, Any]] = CodecOptions(
            uuid_representation=UuidRepresentation.STANDARD
        )
        self.collection = self.database.get_collection(
            "conversation_item", codec_options=standard_opts
        )

    async def insert(
        self, document: ConversationItemDocument
    ) -> ConversationItemDocument:
        result = await self.collection.insert_one(
            document.model_dump(by_alias=True, exclude_none=True)
        )
        assert document.id == result.inserted_id
        return document

    async def delete_by_conversation(self, conversation_id: str) -> int:
        result = await self.collection.delete_many({"conversation_id": conversation_id})
        return result.deleted_count

    async def list_by_conversation(
        self,
        conversation_id: str,
        page_size: int,
        page_token: str | None,
        order: Literal["asc", "desc"],
    ) -> tuple[list[TaskDocument | MessageDocument], int, str | None]:
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

        def _from_dict(document: dict[str, Any]) -> TaskDocument | MessageDocument:
            if document["kind"] == ConversationItemKind.TASK:
                return TaskDocument.model_validate(document)
            elif document["kind"] == ConversationItemKind.MESSAGE:
                return MessageDocument.model_validate(document)
            else:
                raise ValueError(f"Unknown ConversationItemKind: {document['kind']}")

        conversation_items = [_from_dict(document) for document in documents]
        next_page_token = encode_page_token(documents[-1]["_id"])

        return conversation_items, total, next_page_token


if __name__ == "__main__":
    ...
