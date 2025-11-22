from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, Field

from chat.common.parts import Part, TextPart
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
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional key-value metadata. Useful for adding extra information. "
        "For example, specifying the agent to handle user message through 'agent' key.",
    )

    def text_content(self) -> str | None:
        texts: list[str] = []
        last_part: Part | None = None
        for part in self.content:
            if isinstance(part, TextPart):
                # Adjacent text parts should be joined together
                # But if there're other parts in between (like tool calls)
                # they should have newlines between them
                if isinstance(last_part, TextPart):
                    texts[-1] += part.text
                else:
                    texts.append(part.text)
            last_part = part
        if not texts:
            return None

        return "\n\n".join(texts)


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
