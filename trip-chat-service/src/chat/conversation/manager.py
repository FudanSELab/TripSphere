from abc import ABC, abstractmethod
from typing import Any, Literal, TypedDict

from chat.models import Conversation, ConversationItem


class ConversationManager(ABC):
    @abstractmethod
    async def create_conversation(
        self, user_id: str, metadata: dict[str, Any] | None = None
    ) -> Conversation: ...

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> None: ...

    @abstractmethod
    async def update_metadata(
        self, conversation_id: str, metadata: dict[str, Any] | None = None
    ) -> Conversation: ...

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Conversation: ...


class ListItemsResult(TypedDict):
    items: list[ConversationItem]
    next_page_token: str | None
    total_size: int


class ConversationItemManager(ABC):
    @abstractmethod
    async def get_item(self, item_id: str) -> ConversationItem: ...

    @abstractmethod
    async def paginate_items(
        self,
        conversation_id: str,
        page_size: int,
        page_token: str | None = None,
        order: Literal["asc", "desc"] = "desc",
    ) -> ListItemsResult: ...

    @abstractmethod
    async def extend_items(
        self, conversation_id: str, items: list[ConversationItem]
    ) -> None: ...
