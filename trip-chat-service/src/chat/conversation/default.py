from datetime import datetime
from typing import Any, Literal

from a2a.types import Message, Task, TaskStatus

from chat.conversation.manager import ConversationManager
from chat.conversation.models import (
    Conversation,
    ConversationItem,
)
from chat.storage.mongodb.collections import (
    ConversationCollection,
    ConversationItemCollection,
)
from chat.storage.mongodb.schema import (
    ConversationDocument,
    MessageDocument,
    TaskDocument,
)


class DefaultConversationManager(ConversationManager):
    def __init__(
        self,
        conversation_collection: ConversationCollection,
        conversation_item_collection: ConversationItemCollection,
    ) -> None:
        self.conversation_collection = conversation_collection
        self.conversation_item_collection = conversation_item_collection

    async def create_conversation(
        self, user_id: str, metadata: dict[str, Any] | None = None
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            created_at=datetime.now(),
            metadata=metadata,
        )
        document = await self.conversation_collection.insert(
            ConversationDocument(
                user_id=conversation.user_id,
                created_at=conversation.created_at,
                metadata=conversation.metadata,
            )
        )
        conversation.conversation_id = document.id
        return conversation

    async def delete_conversation(self, conversation_id: str) -> None:
        await self.conversation_collection.delete_by_id(conversation_id)

    async def update_conversation(
        self, conversation_id: str, metadata: dict[str, Any] | None = None
    ) -> Conversation:
        document = await self.conversation_collection.update_metadata(
            conversation_id, metadata or {}
        )
        return Conversation(
            conversation_id=document.id,
            user_id=document.user_id,
            created_at=document.created_at,
            metadata=document.metadata,
        )

    async def get_conversation(self, conversation_id: str) -> Conversation:
        document = await self.conversation_collection.find_by_id(conversation_id)
        if document is None:
            raise ValueError(f"Conversation with ID {conversation_id} not found.")
        return Conversation(
            conversation_id=document.id,
            user_id=document.user_id,
            created_at=document.created_at,
            metadata=document.metadata,
        )

    async def list_conversation_items(
        self,
        conversation_id: str,
        page_size: int,
        page_token: str | None = None,
        order: Literal["asc", "desc"] = "desc",
    ) -> tuple[list[ConversationItem], int, str | None]:
        result = await self.conversation_item_collection.list_by_conversation(
            conversation_id=conversation_id,
            page_size=page_size,
            page_token=page_token,
            order=order,
        )
        documents, total, next_page_token = result

        def _from_document(document: MessageDocument | TaskDocument) -> Message | Task:
            if isinstance(document, MessageDocument):
                return Message(
                    message_id=document.id or "MESSAGE_ID_NOT_SET",
                    context_id=document.conversation_id,
                    role=document.role,
                    parts=document.parts,
                    task_id=document.task_id,
                    metadata=document.metadata,
                )
            else:
                task_status = TaskStatus(
                    state=document.status.state,
                    timestamp=document.status.timestamp.isoformat(),
                )
                return Task(
                    id=document.id or "TASK_ID_NOT_SET",
                    context_id=document.conversation_id,
                    status=task_status,
                    artifacts=document.artifacts,
                    metadata=document.metadata,
                )

        conversation_items = [
            ConversationItem(
                created_at=document.created_at, content=_from_document(document)
            )
            for document in documents
        ]
        return conversation_items, total, next_page_token
