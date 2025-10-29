from abc import ABC, abstractmethod
from typing import Any, Literal, TypedDict

from chat.conversation.models import Conversation, ConversationItem


class ListConversationItemsResult(TypedDict):
    items: list[ConversationItem]
    total_count: int
    next_page_token: str | None


class ConversationManager(ABC):
    @abstractmethod
    async def create_conversation(
        self, user_id: str, metadata: dict[str, Any] | None = None
    ) -> Conversation: ...

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> None: ...

    @abstractmethod
    async def update_conversation(
        self, conversation_id: str, metadata: dict[str, Any] | None = None
    ) -> Conversation: ...

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Conversation: ...

    @abstractmethod
    async def list_conversation_items(
        self,
        conversation_id: str,
        page_size: int,
        page_token: str | None = None,
        order: Literal["asc", "desc"] = "desc",
    ) -> ListConversationItemsResult: ...
