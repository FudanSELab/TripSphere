from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from a2a.types import Artifact, Part, Role, TaskState
from pydantic import BaseModel, BeforeValidator, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class ConversationItemKind(StrEnum):
    TASK = "task"
    MESSAGE = "message"


class ConversationItemDocument(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    conversation_id: PyObjectId
    created_at: datetime
    metadata: dict[str, Any] | None = Field(default=None)


class MessageDocument(ConversationItemDocument):
    task_id: PyObjectId | None = Field(default=None)
    role: Role
    parts: list[Part]


class TaskStatus(BaseModel):
    state: TaskState
    message_id: PyObjectId | None = Field(default=None)
    timestamp: datetime


class TaskDocument(ConversationItemDocument):
    status: TaskStatus
    artifacts: list[Artifact] | None = Field(default=None)
    history: list[PyObjectId] | None = Field(
        default=None, description="List of historical interaction message IDs."
    )


class ConversationDocument(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    user_id: str
    created_at: datetime
    metadata: dict[str, Any] | None = Field(default=None)


if __name__ == "__main__":
    ...
