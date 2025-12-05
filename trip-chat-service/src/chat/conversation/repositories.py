from abc import ABC, abstractmethod
from typing import Any, Literal

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection

from chat.conversation.models import Conversation, Message
from chat.utils.pagination import decode_uuid_cursor, encode_uuid_cursor


class ConversationRepository(ABC):
    @abstractmethod
    async def save(self, conversation: Conversation) -> None: ...

    @abstractmethod
    async def find_by_id(self, conversation_id: str) -> Conversation | None: ...

    @abstractmethod
    async def list_by_user(
        self,
        user_id: str,
        limit: int,
        token: str | None = None,
        direction: Literal["forward", "backward"] = "backward",
    ) -> tuple[list[Conversation], str | None]: ...


class MessageRepository(ABC):
    @abstractmethod
    async def save(self, message: Message) -> None: ...

    @abstractmethod
    async def find_by_id(self, message_id: str) -> Message | None: ...

    @abstractmethod
    async def list_by_conversation(
        self,
        conversation_id: str,
        limit: int,
        token: str | None = None,
        direction: Literal["forward", "backward"] = "backward",
    ) -> tuple[list[Message], str | None]:
        """
        List Messages of Conversation with cursor-based pagination.

        Arguments:
            conversation_id: ID of the Conversation to fetch Messages from.
            limit: Maximum number of Messages to return.
            token: Optional pagination token from the previous call.
            direction: Determines the sort order of Messages.

        Returns:
            A tuple containing a Message list and an optional next pagination token.
        """
        ...


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

    async def list_by_user(
        self,
        user_id: str,
        limit: int,
        token: str | None = None,
        direction: Literal["forward", "backward"] = "backward",
    ) -> tuple[list[Conversation], str | None]:
        query: dict[str, Any] = {"user_id": user_id}
        if last_id := decode_uuid_cursor(token):
            # When direction is "backward", fetch docs with _id < last_id
            query["_id"] = {("$lt" if direction == "backward" else "$gt"): last_id}

        cursor = (
            self.collection.find(query)
            .sort("_id", DESCENDING if direction == "backward" else ASCENDING)
            .limit(limit=limit)
        )
        documents = await cursor.to_list()

        if len(documents) == 0:
            return [], None  # No more results

        conversations = [Conversation.model_validate(doc) for doc in documents]
        next_token = encode_uuid_cursor(documents[-1]["_id"])
        return conversations, next_token


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

    async def list_by_conversation(
        self,
        conversation_id: str,
        limit: int,
        token: str | None = None,
        direction: Literal["forward", "backward"] = "backward",
    ) -> tuple[list[Message], str | None]:
        query: dict[str, Any] = {"conversation_id": conversation_id}
        if last_id := decode_uuid_cursor(token):
            # When direction is "backward", fetch docs with _id < last_id
            query["_id"] = {("$lt" if direction == "backward" else "$gt"): last_id}

        cursor = (
            self.collection.find(query)
            .sort("_id", DESCENDING if direction == "backward" else ASCENDING)
            .limit(limit=limit)
        )
        documents = await cursor.to_list()

        if len(documents) == 0:
            return [], None  # No more results

        messages = [Message.model_validate(doc) for doc in documents]
        next_token = encode_uuid_cursor(documents[-1]["_id"])
        return messages, next_token
