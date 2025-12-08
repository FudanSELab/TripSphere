from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, Field

from chat.common.parts import Part, TextPart
from chat.utils.uuid import uuid7


class Author(BaseModel):
    role: Literal["user", "agent"]
    name: str | None = Field(
        default=None,
        description="Optional name of the user/agent.",
    )

    @classmethod
    def user(cls, name: str | None = None) -> Self:
        return cls(role="user", name=name)

    @classmethod
    def agent(cls, name: str | None = None) -> Self:
        return cls(role="agent", name=name)


class Message(BaseModel):
    message_id: str = Field(
        alias="_id",
        default_factory=lambda: str(uuid7()),
        description="Unique identifier of the Message.",
    )
    conversation_id: str = Field(
        ..., description="ID of the Conversation that this Message belongs to."
    )
    author: Author = Field(..., description="Author of the Message.")
    content: list[Part] = Field(
        default_factory=list[Part],
        description="Content Parts, which are to be rendered, of the Message.",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional key-value metadata. Useful for adding extra information.",
    )

    def text_content(self) -> str | None:
        texts: list[str] = []
        last_part: Part | None = None
        for part in self.content:
            if isinstance(part.root, TextPart):
                # Adjacent text parts should be joined together
                # But if there're other parts in between (like tool calls)
                # they should have newlines between them
                if last_part and isinstance(last_part.root, TextPart):
                    texts[-1] += part.root.text
                else:
                    texts.append(part.root.text)
            last_part = part
        if not texts:
            return None
        return "\n\n".join(texts)


class Conversation(BaseModel):
    conversation_id: str = Field(
        alias="_id",
        default_factory=lambda: str(uuid7()),
        description="Unique identifier of the Conversation.",
    )
    title: str | None = Field(default=None, description="Title of the Conversation.")
    user_id: str = Field(..., description="ID of the Conversation's owner.")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] | None = Field(default=None)
