from typing import Any

from chat.common.parts import Part
from chat.conversation.entities import Author, Conversation, Message
from chat.conversation.repositories import ConversationRepository, MessageRepository
from chat.task.entities import Task


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

    async def add_text_query(
        self,
        conversation: Conversation,
        query: str,
        associated_task: Task | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """
        Appends a user text message to the conversation.

        Arguments:
            conversation: The conversation to which the query is appended.
            query: The user's chat query message.
            associated_task: Optional Task associated with this message.
            metadata: Optional metadata for the message.
                Useful for specifying the agent to handle this user message.

        Returns:
            The newly appended query message.
        """
        query_message = Message(
            conversation_id=conversation.conversation_id,
            task_id=associated_task.task_id if associated_task else None,
            author=Author.user(),
            content=[Part.from_text(query)],
            metadata=metadata,
        )
        await self.message_repository.save(query_message)
        return query_message

    async def add_empty_answer(
        self, conversation: Conversation, associated_task: Task | None = None
    ) -> Message:
        response_message = Message(
            conversation_id=conversation.conversation_id,
            task_id=associated_task.task_id if associated_task else None,
            author=Author.agent(),
        )
        await self.message_repository.save(response_message)
        return response_message

    async def list_messages(
        self,
        conversation: Conversation,
        results_per_page: int,
        cursor: str | None = None,
    ) -> tuple[list[Message], str | None]:
        messages, next_cursor = await self.message_repository.list_by_conversation(
            conversation_id=conversation.conversation_id,
            limit=results_per_page,
            token=cursor,
            direction="backward",
        )
        return messages, next_cursor
