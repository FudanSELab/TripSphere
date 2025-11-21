from typing import Any

from chat.common.parts import Part
from chat.conversation.entities import Author, Conversation, Message
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

    async def append_text_query(
        self, conversation: Conversation, query: str
    ) -> Message:
        """
        Appends a user text message to the conversation.

        Arguments:
            conversation: The conversation to which the query is appended.
            query: The user's chat query message.

        Returns:
            The newly appended query message.
        """
        query_message = Message(
            conversation_id=conversation.conversation_id,
            author=Author.user(),
            content=[Part.from_text(query)],
        )
        await self.message_repository.save(query_message)
        return query_message

    async def delete_conversation(self, conversation: Conversation) -> None:
        raise NotImplementedError

    async def append_agent_answer(
        self,
        conversation: Conversation,
        author: Author,
        answer_parts: list[Part],
        task_id: str | None = None,
    ) -> Message:
        response_message = Message(
            conversation_id=conversation.conversation_id,
            author=author,
            content=answer_parts,
            task_id=task_id,
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
