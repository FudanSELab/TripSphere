from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, Field

from chat.common.parts import Part
from chat.utils.uuid import uuid7


class Author(BaseModel):
    role: Literal["user", "agent", "system"]
    name: str | None = Field(
        default=None,
        description="Optional name of the user/agent.",
        examples=["chat-assistant"],
    )

    @classmethod
    def user(cls, name: str | None = None) -> Self:
        return cls(role="user", name=name)

    @classmethod
    def agent(cls, name: str | None = None) -> Self:
        return cls(role="agent", name=name)

    @classmethod
    def system(cls, name: str | None = None) -> Self:
        return cls(role="system", name=name)


class Message(BaseModel):
    message_id: str = Field(
        alias="_id",
        default_factory=lambda: str(uuid7()),
        examples=["019a3b16-4759-767c-bc8c-eb3e094c71b9"],
    )
    conversation_id: str = Field(
        ..., description="Conversation ID this message belongs to."
    )
    task_id: str | None = Field(
        default=None, description="Optional Task ID associated with this message."
    )
    author: Author = Field(..., description="Author of the message.")
    content: list[Part] = Field(
        default_factory=list[Part],
        description="Content parts of the message."
        "It stores the final content to be rendered, if associated with a task.",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] | None = Field(default=None)


class Conversation(BaseModel):
    conversation_id: str = Field(
        alias="_id",
        default_factory=lambda: str(uuid7()),
        examples=["019a3b16-4759-767c-bc8c-eb3e094c71b9"],
    )
    title: str | None = Field(default=None, description="Title of the conversation.")
    user_id: str = Field(..., description="ID of the conversation's owner.")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] | None = Field(default=None)
