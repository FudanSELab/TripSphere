from typing import Any, Literal

from chat.conversation.manager import (
    ConversationItemManager,
    ConversationManager,
    ListItemsResult,
)
from chat.exceptions import ConversationItemNotFoundError, ConversationNotFoundError
from chat.infrastructure.mongodb.repositories import (
    ConversationItemRepository,
    ConversationRepository,
)
from chat.models import Conversation, ConversationItem


class DefaultConversationManager(ConversationManager):
    def __init__(self, conversation_repository: ConversationRepository) -> None:
        self.conversation_repository = conversation_repository

    async def create_conversation(
        self, user_id: str, metadata: dict[str, Any] | None = None
    ) -> Conversation:
        conversation = Conversation(user_id=user_id, metadata=metadata)
        await self.conversation_repository.save(conversation)
        return conversation

    async def delete_conversation(self, conversation_id: str) -> None:
        await self.conversation_repository.remove_by_id(conversation_id)

    async def update_metadata(
        self, conversation_id: str, metadata: dict[str, Any] | None = None
    ) -> Conversation:
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        conversation.metadata = metadata
        await self.conversation_repository.save(conversation)
        return conversation

    async def get_conversation(self, conversation_id: str) -> Conversation:
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        return conversation


class DefaultConversationItemManager(ConversationItemManager):
    def __init__(
        self, conversation_item_repository: ConversationItemRepository
    ) -> None:
        self.conversation_item_repository = conversation_item_repository

    async def get_item(self, item_id: str) -> ConversationItem:
        item = await self.conversation_item_repository.find_by_id(item_id)
        if item is None:
            raise ConversationItemNotFoundError(item_id)
        return item

    async def paginate_items(
        self,
        conversation_id: str,
        page_size: int,
        page_token: str | None = None,
        order: Literal["asc", "desc"] = "desc",
    ) -> ListItemsResult:
        (
            items,
            total_size,
            next_page_token,
        ) = await self.conversation_item_repository.find_all_by_conversation_id(
            conversation_id=conversation_id,
            page_size=page_size,
            page_token=page_token,
            order=order,
        )
        return ListItemsResult(
            items=items,
            total_size=total_size,
            next_page_token=next_page_token,
        )

    async def extend_items(
        self, conversation_id: str, items: list[ConversationItem]
    ) -> None: ...
