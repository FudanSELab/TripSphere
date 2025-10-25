from datetime import datetime
from typing import Any

from a2a.types import Message, Task
from pydantic import BaseModel, Field


class Conversation(BaseModel):
    conversation_id: str | None = Field(default=None)
    user_id: str
    created_at: datetime
    metadata: dict[str, Any] | None = Field(default=None)


class ConversationItem(BaseModel):
    created_at: datetime
    content: Message | Task


if __name__ == "__main__":
    ...
