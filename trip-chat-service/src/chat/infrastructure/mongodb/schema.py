from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from chat.models import (
    Artifact,
    Conversation,
    ConversationItem,
    Message,
    MessageRole,
    MessageSnapshot,
    Part,
    Task,
    TaskSnapshot,
    TaskStatus,
)


class BaseDocument(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )


class ConversationDocument(BaseDocument):
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime
    metadata: dict[str, Any] | None

    @classmethod
    def from_model(cls, conversation: Conversation) -> Self:
        return cls(
            _id=conversation.conversation_id,
            user_id=conversation.user_id,
            created_at=conversation.created_at,
            metadata=conversation.metadata,
        )

    def to_model(self) -> Conversation:
        return Conversation(
            conversation_id=self.id,
            user_id=self.user_id,
            created_at=self.created_at,
            metadata=self.metadata,
        )


class ConversationItemDocument(BaseDocument):
    id: str = Field(alias="_id")
    conversation_id: str
    content: TaskSnapshot | MessageSnapshot
    created_at: datetime

    @classmethod
    def from_model(cls, item: ConversationItem) -> Self:
        return cls(
            _id=item.item_id,
            conversation_id=item.conversation_id,
            content=item.content,
            created_at=item.created_at,
        )

    def to_model(self) -> ConversationItem:
        return ConversationItem(
            item_id=self.id,
            conversation_id=self.conversation_id,
            content=self.content,
            created_at=self.created_at,
        )


class ArtifactDocument(BaseDocument):
    id: str = Field(alias="_id")
    description: str | None
    extension: list[str] | None
    name: str | None
    parts: list[Part]
    created_at: datetime
    updated_at: datetime | None
    metadata: dict[str, Any] | None

    @classmethod
    def from_model(cls, artifact: Artifact) -> Self:
        return cls(
            _id=artifact.artifact_id,
            description=artifact.description,
            extension=artifact.extensions,
            name=artifact.name,
            parts=artifact.parts,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
            metadata=artifact.metadata,
        )

    def to_model(self) -> Artifact:
        return Artifact(
            artifact_id=self.id,
            description=self.description,
            extensions=self.extension,
            name=self.name,
            parts=self.parts,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata,
        )


class TaskDocument(BaseDocument):
    id: str = Field(alias="_id")
    context_id: str | None
    status: TaskStatus
    artifacts: list[str] | None
    created_at: datetime
    metadata: dict[str, Any] | None

    @classmethod
    def from_model(cls, task: Task) -> Self:
        return cls(
            _id=task.task_id,
            context_id=task.context_id,
            status=task.status,
            artifacts=task.artifacts,
            created_at=task.created_at,
            metadata=task.metadata,
        )

    def to_model(self) -> Task:
        return Task(
            task_id=self.id,
            context_id=self.context_id,
            status=self.status,
            artifacts=self.artifacts,
            created_at=self.created_at,
            metadata=self.metadata,
        )


class MessageDocument(BaseDocument):
    id: str = Field(alias="_id")
    context_id: str | None
    role: MessageRole
    parts: list[Part]
    extensions: list[str] | None
    reference_task_ids: list[str] | None
    created_at: datetime
    metadata: dict[str, Any] | None

    @classmethod
    def from_model(cls, message: Message) -> Self:
        return cls(
            _id=message.message_id,
            context_id=message.context_id,
            role=message.role,
            parts=message.parts,
            extensions=message.extensions,
            reference_task_ids=message.reference_task_ids,
            created_at=message.created_at,
            metadata=message.metadata,
        )

    def to_model(self) -> Message:
        return Message(
            message_id=self.id,
            context_id=self.context_id,
            role=self.role,
            parts=self.parts,
            extensions=self.extensions,
            reference_task_ids=self.reference_task_ids,
            created_at=self.created_at,
            metadata=self.metadata,
        )
