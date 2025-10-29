from datetime import datetime
from typing import Any

from a2a.types import Message, Task
from pydantic import BaseModel, Field, computed_field, field_validator


class Conversation(BaseModel):
    conversation_id: str | None = Field(default=None)
    user_id: str
    created_at: datetime
    metadata: dict[str, Any] | None = Field(default=None)


class ConversationItem(BaseModel):
    created_at: datetime
    content: Message | Task

    @computed_field
    @property
    def item_id(self) -> str:
        if isinstance(self.content, Task):
            return self.content.id
        else:
            return self.content.message_id

    @field_validator("content", mode="after")
    @classmethod
    def validate_content(cls, value: Message | Task) -> Message | Task:
        if isinstance(value, Task) and value.history:
            raise ValueError("ConversationItem Task must not contain history.")
        return value


if __name__ == "__main__":
    ...
