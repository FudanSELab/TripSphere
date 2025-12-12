from abc import ABC, abstractmethod
from typing import Any, Literal

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection

from chat.conversation.models import Conversation, Message
from chat.utils.pagination import (
    CursorPagination,
    decode_uuid_cursor,
    encode_uuid_cursor,
)


class ConversationRepository(ABC):
    @abstractmethod
    async def save(self, conversation: Conversation) -> None: ...

    @abstractmethod
    async def find_by_id(self, conversation_id: str) -> Conversation | None: ...

    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        limit: int,
        direction: Literal["forward", "backward"],
        token: str | None = None,
    ) -> CursorPagination[str, Conversation]: ...

    @abstractmethod
    async def delete_by_id(self, conversation_id: str) -> None: ...


class MessageRepository(ABC):
    @abstractmethod
    async def save(self, message: Message) -> None: ...

    @abstractmethod
    async def find_by_id(self, message_id: str) -> Message | None: ...

    @abstractmethod
    async def find_by_conversation(
        self,
        conversation_id: str,
        limit: int,
        direction: Literal["forward", "backward"],
        token: str | None = None,
    ) -> CursorPagination[str, Message]: ...

    @abstractmethod
    async def delete_by_conversation(self, conversation_id: str) -> None: ...


class MongoConversationRepository(ConversationRepository):
    COLLECTION_NAME = "conversations"

    def __init__(self, collection: AsyncCollection[dict[str, Any]]) -> None:
        self.collection = collection

    async def save(self, conversation: Conversation) -> None:
        document = conversation.model_dump(by_alias=True)
        await self.collection.replace_one(
            {"_id": document["_id"]}, document, upsert=True
        )

    async def find_by_id(self, conversation_id: str) -> Conversation | None:
        document = await self.collection.find_one({"_id": conversation_id})
        if document is not None:
            return Conversation.model_validate(document)
        return None

    async def find_by_user(
        self,
        user_id: str,
        limit: int,
        direction: Literal["forward", "backward"],
        token: str | None = None,
    ) -> CursorPagination[str, Conversation]:
        query: dict[str, Any] = {"user_id": user_id}
        if last_id := decode_uuid_cursor(token):
            # When direction is "backward", fetch docs with _id < last_id
            query["_id"] = {("$lt" if direction == "backward" else "$gt"): last_id}

        cursor = (
            self.collection.find(query)
            .sort("_id", DESCENDING if direction == "backward" else ASCENDING)
            .limit(
                limit=limit + 1
            )  # Fetch one extra to determine if there's a next page
        )
        documents = await cursor.to_list()
        conversations = [Conversation.model_validate(doc) for doc in documents]

        if len(documents) <= limit:
            return CursorPagination[str, Conversation](
                items=conversations, results_per_page=limit, cursor=None
            )  # No more results

        # Use the ID of the last item being returned (not the extra one)
        next_token = encode_uuid_cursor(documents[limit - 1]["_id"])
        return CursorPagination[str, Conversation](
            items=conversations[:limit], results_per_page=limit, cursor=next_token
        )

    async def delete_by_id(self, conversation_id: str) -> None:
        await self.collection.delete_one({"_id": conversation_id})


class MongoMessageRepository(MessageRepository):
    COLLECTION_NAME = "messages"

    def __init__(self, collection: AsyncCollection[dict[str, Any]]) -> None:
        self.collection = collection

    async def save(self, message: Message) -> None:
        document = message.model_dump(by_alias=True)
        await self.collection.replace_one(
            {"_id": document["_id"]}, document, upsert=True
        )

    async def find_by_id(self, message_id: str) -> Message | None:
        document = await self.collection.find_one({"_id": message_id})
        if document is not None:
            return Message.model_validate(document)
        return None

    async def find_by_conversation(
        self,
        conversation_id: str,
        limit: int,
        direction: Literal["forward", "backward"],
        token: str | None = None,
    ) -> CursorPagination[str, Message]:
        query: dict[str, Any] = {"conversation_id": conversation_id}
        if last_id := decode_uuid_cursor(token):
            # When direction is "backward", fetch docs with _id < last_id
            query["_id"] = {("$lt" if direction == "backward" else "$gt"): last_id}

        cursor = (
            self.collection.find(query)
            .sort("_id", DESCENDING if direction == "backward" else ASCENDING)
            .limit(
                limit=limit + 1
            )  # Fetch one extra to determine if there's a next page
        )
        documents = await cursor.to_list()
        messages = [Message.model_validate(doc) for doc in documents]

        if len(documents) <= limit:
            return CursorPagination[str, Message](
                items=messages, results_per_page=limit, cursor=None
            )  # No more results

        # Use the ID of the last item being returned (not the extra one)
        next_token = encode_uuid_cursor(documents[limit - 1]["_id"])
        return CursorPagination[str, Message](
            items=messages[:limit], results_per_page=limit, cursor=next_token
        )

    async def delete_by_conversation(self, conversation_id: str) -> None:
        await self.collection.delete_many({"conversation_id": conversation_id})
