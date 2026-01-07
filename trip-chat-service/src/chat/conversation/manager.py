from typing import Any, Literal

from chat.common.parts import Part
from chat.conversation.models import Author, Conversation, Message
from chat.conversation.repository import ConversationRepository, MessageRepository
from chat.utils.pagination import CursorPagination


class ConversationManager:
    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
    ) -> None:
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository

    async def create_conversation(
        self,
        user_id: str,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        conversation = Conversation(title=title, user_id=user_id, metadata=metadata)
        await self.conversation_repository.save(conversation)
        return conversation

    async def delete_conversation(self, conversation: Conversation) -> None:
        await self.message_repository.delete_by_conversation(
            conversation_id=conversation.conversation_id
        )
        await self.conversation_repository.delete_by_id(
            conversation_id=conversation.conversation_id
        )

    async def add_user_query(
        self,
        conversation: Conversation,
        content: list[Part],
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        query_message = Message(
            conversation_id=conversation.conversation_id,
            author=Author.user("default"),
            content=content,
            metadata=metadata,
        )
        await self.message_repository.save(query_message)
        return query_message

    async def list_conversation_messages(
        self,
        conversation: Conversation,
        results_per_page: int,
        direction: Literal["forward", "backward"] = "backward",
        cursor: str | None = None,
    ) -> CursorPagination[str, Message]:
        pagination = await self.message_repository.list_by_conversation(
            conversation_id=conversation.conversation_id,
            limit=results_per_page,
            direction=direction,
            token=cursor,
        )
        return pagination
