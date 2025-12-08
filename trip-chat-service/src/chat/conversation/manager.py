from typing import Any, Literal

from chat.common.parts import Part
from chat.conversation.models import Author, Conversation, Message
from chat.conversation.repositories import ConversationRepository, MessageRepository


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
        raise NotImplementedError

    async def add_user_query(
        self,
        conversation: Conversation,
        content: list[Part],
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """
        Appends a user Message to the Conversation.

        Arguments:
            conversation: The Conversation to which the query is appended.
            query: The user's chat query Message.
            metadata: Optional metadata for the Message.
                Useful for specifying the agent to handle this query.

        Returns:
            The newly appended query Message.
        """
        query_message = Message(
            conversation_id=conversation.conversation_id,
            author=Author.user("default"),
            content=content,
            metadata=metadata,
        )
        await self.message_repository.save(query_message)
        return query_message

    async def list_messages(
        self,
        conversation: Conversation,
        results_per_page: int,
        cursor: str | None = None,
        direction: Literal["forward", "backward"] = "backward",
    ) -> tuple[list[Message], str | None]:
        messages, next_cursor = await self.message_repository.list_by_conversation(
            conversation_id=conversation.conversation_id,
            limit=results_per_page,
            token=cursor,
            direction=direction,
        )
        return messages, next_cursor
