from datetime import datetime
from enum import StrEnum
from typing import Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    model_validator,
)

from chat.utils.uuid import uuid7


class TextPart(BaseModel):
    """
    TextPart (value object).
    """

    text: str = Field(description="String content of the part.")
    metadata: dict[str, Any] | None = Field(default=None)
    model_config = ConfigDict(frozen=True)


class FilePart(BaseModel):
    """
    FilePart (value object).
    """

    uri: str | None = Field(default=None, description="URI pointing to the file.")
    bytes: str | None = Field(default=None, description="Base64-encoded file content.")
    mime_type: str | None = Field(default=None, examples=["application/pdf"])
    name: str | None = Field(default=None, examples=["document.pdf"])
    metadata: dict[str, Any] | None = Field(default=None)
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def check_bytes_xor_uri(self) -> Self:
        if self.bytes and self.uri:
            raise ValueError("Only one of 'bytes' or 'uri' should be provided.")
        if (not self.bytes) and (not self.uri):
            raise ValueError("One of 'bytes' or 'uri' must be provided.")
        return self


class DataPart(BaseModel):
    """
    DataPart (value object).
    """

    data: dict[str, Any] = Field(description="Structured data content.")
    metadata: dict[str, Any] | None = Field(default=None)
    model_config = ConfigDict(frozen=True)


class Part(RootModel[TextPart | FilePart | DataPart]):
    """
    Part (value object) can be one of TextPart, FilePart, or DataPart.
    """

    root: TextPart | FilePart | DataPart


class MessageRole(StrEnum):
    UNSPECIFIED = "unspecified"
    USER = "user"
    AGENT = "agent"


class MessageSnapshot(BaseModel):
    """
    Snapshot of a Message (value object) at a specific point in time.
    """

    message_id: str
    context_id: str | None
    role: MessageRole
    parts: list[Part]
    extensions: list[str] | None
    reference_task_ids: list[str] | None
    metadata: dict[str, Any] | None
    model_config = ConfigDict(frozen=True)

    def text_content(self) -> str:
        texts = [p.root.text for p in self.parts if isinstance(p.root, TextPart)]
        return "\n".join(texts)


class Message(BaseModel):
    """
    Represents a single message in the conversation between a user and an agent.
    After persistence, a persisted Message will never be modified or deleted.
    """

    message_id: str = Field(
        default_factory=lambda: str(uuid7()),
        examples=["019a3b16-4759-767c-bc8c-eb3e094c71b9"],
    )
    context_id: str | None = Field(
        default=None, description="It is usually a Conversation ID."
    )
    role: MessageRole = Field(description="Role of the message sender.")
    parts: list[Part] = Field(
        description="List of content parts that make up the message."
    )
    extensions: list[str] | None = Field(
        default=None,
        description="URIs of extensions that are relevant to this message.",
    )
    reference_task_ids: list[str] | None = Field(
        default=None,
        description="List of task IDs that this message references.",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp indicating when the message was created.",
        examples=[datetime(2023, 10, 27, 10, 0, 0)],
    )
    metadata: dict[str, Any] | None = Field(default=None)

    @classmethod
    def from_text(cls, text: str, role: MessageRole) -> Self:
        part = Part.model_validate(TextPart(text=text))
        return cls(role=role, parts=[part])

    def text_content(self) -> str:
        texts = [p.root.text for p in self.parts if isinstance(p.root, TextPart)]
        return "\n".join(texts)


class ArtifactSnapshot(BaseModel):
    """
    Snapshot of an Artifact (value object) at a specific point in time.
    """

    artifact_id: str
    description: str | None
    extensions: list[str] | None
    name: str | None
    parts: list[Part]
    metadata: dict[str, Any] | None
    model_config = ConfigDict(frozen=True)

    def text_content(self) -> str:
        texts = [p.root.text for p in self.parts if isinstance(p.root, TextPart)]
        return "\n".join(texts)


class Artifact(BaseModel):
    artifact_id: str = Field(
        default_factory=lambda: str(uuid7()),
        examples=["019a3b16-4759-767c-bc8c-eb3e094c71b9"],
    )
    description: str | None = Field(
        default=None, description="Optional description of the artifact."
    )
    extensions: list[str] | None = Field(
        default=None,
        description="URIs of extensions that are relevant to this artifact.",
    )
    name: str | None = Field(
        default=None, description="Optional name for the artifact."
    )
    parts: list[Part] = Field(
        description="List of content parts that make up the artifact."
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)

    @classmethod
    def from_text(cls, text: str) -> Self:
        part = Part.model_validate(TextPart(text=text))
        return cls(parts=[part])

    def text_content(self) -> str:
        texts = [p.root.text for p in self.parts if isinstance(p.root, TextPart)]
        return "\n".join(texts)


class TaskState(StrEnum):
    """
    Defines the lifecycle states of a Task.
    """

    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    REJECTED = "rejected"
    AUTH_REQUIRED = "auth-required"
    UNKNOWN = "unknown"


class TaskStatus(BaseModel):
    """
    TaskStatus (value object) represents the status of a task at a point in time.
    """

    message: MessageSnapshot | None = Field(
        default=None,
        description="Snapshot of message providing more details about current status.",
    )
    state: TaskState = Field(description="The current state of the task's lifecycle.")
    timestamp: datetime | None = Field(
        default=None,
        description="Datetime indicating when this status was recorded.",
        examples=[datetime(2023, 10, 27, 10, 0, 0)],
    )
    model_config = ConfigDict(frozen=True)


class TaskSnapshot(BaseModel):
    """
    Snapshot of a Task (value object) at a specific point in time.
    """

    task_id: str
    context_id: str | None
    status: TaskStatus
    artifacts: list[ArtifactSnapshot] | None
    history: list[MessageSnapshot] | None
    metadata: dict[str, Any] | None
    model_config = ConfigDict(frozen=True)


class Task(BaseModel):
    """
    Represents a single, stateful operation between a client and an agent.
    """

    task_id: str = Field(
        default_factory=lambda: str(uuid7()),
        examples=["019a3b16-4759-767c-bc8c-eb3e094c71b9"],
    )
    context_id: str | None = Field(
        default=None, description="It is usually a Conversation ID."
    )
    status: TaskStatus = Field(description="The current status of the task.")
    artifacts: list[str] | None = Field(
        default=None, description="List of artifact IDs associated with this task."
    )
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] | None = Field(default=None)

    @property
    def updated_at(self) -> datetime | None:
        return self.status.timestamp


class Conversation(BaseModel):
    """
    Represents a conversation between a user and an agent.
    """

    conversation_id: str = Field(default_factory=lambda: str(uuid7()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] | None = Field(default=None)


class ConversationItem(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid7()))
    conversation_id: str
    content: TaskSnapshot | MessageSnapshot = Field(
        description="The content of the conversation item. "
        "Snapshot of either a Task or a Message. "
        "Message is stateless while a task is stateful."
    )
    created_at: datetime = Field(default_factory=datetime.now)


class MemoryItem(BaseModel):
    item_id: str = Field(
        default_factory=lambda: str(uuid7()),
        examples=["019a3b16-4759-767c-bc8c-eb3e094c71b9"],
    )
    content: list[Part]
    metadata: dict[str, Any] | None = Field(default=None)

    def text_content(self) -> str:
        texts = [p.root.text for p in self.content if isinstance(p.root, TextPart)]
        return "\n".join(texts)
