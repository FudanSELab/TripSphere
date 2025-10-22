from datetime import datetime
from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field


def convert(value: str | ObjectId | None) -> str | None:
    return str(value) if isinstance(value, ObjectId) else value


DocumentId = Annotated[str | None, Field(alias="_id"), BeforeValidator(convert)]


class ConversationItem(BaseModel):
    item_id: str = Field(description="The ID for internal task/message.")
    created_at: datetime


class ConversationDocument(BaseModel):
    conversation_id: DocumentId
    created_at: datetime
    metadata: dict[str, Any] | None = None


if __name__ == "__main__":
    ...
