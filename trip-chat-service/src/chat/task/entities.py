from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from chat.common.parts import Part
from chat.utils.uuid import uuid7


class TaskState(StrEnum):
    """
    Defines the lifecycle states of a Task.
    """

    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REJECTED = "rejected"
    AUTH_REQUIRED = "auth-required"
    UNKNOWN = "unknown"


class Action(BaseModel):
    action_id: str = Field(
        default_factory=lambda: str(uuid7()),
        examples=["019a3b16-4759-767c-bc8c-eb3e094c71b9"],
    )
    message_id: str | None = Field(
        default=None,
        description="Optional ID of the message that this action contributes to.",
    )
    content: list[Part] | None = Field(
        default=None, description="Content parts of the action."
    )
    action_type: Literal["reply", "tool_use", "pause"]
    created_at: datetime = Field(default_factory=datetime.now)


class TaskStatus(BaseModel):
    state: TaskState = Field(..., description="Current state of the task.")
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of the last status update.",
    )
    action_id: str | None = Field(
        default=None,
        description="Optional action ID associated with the latest status update.",
    )


class Task(BaseModel):
    """
    Represents a local/remote task associated with a conversation.

    [Status 0] ---> [Status 1] --[Action 0, 1]-> [Status 2] ---> ... ---> [Status N]
    """

    task_id: str = Field(
        alias="_id",
        default_factory=lambda: str(uuid7()),
        examples=["019a3b16-4759-767c-bc8c-eb3e094c71b9"],
    )
    task_type: Literal["local", "remote"]
    conversation_id: str = Field(
        ..., description="Conversation ID this task belongs to."
    )
    status: TaskStatus = Field(..., description="Current status of the task.")
    history: list[str] = Field(
        default_factory=list[str],
        description="List of message IDs representing the task's history.",
    )
    actions: list[Action] = Field(
        default_factory=list[Action],
        description="List of actions associated with this task.",
    )
    metadata: dict[str, Any] | None = Field(default=None)
