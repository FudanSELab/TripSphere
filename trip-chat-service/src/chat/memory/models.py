from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from chat.common.parts import Part
from chat.utils.uuid import uuid7


class Memory(BaseModel):
    memory_id: str = Field(
        alias="_id",
        default_factory=lambda: str(uuid7()),
        description="Unique identifier of the Memory.",
    )
    content: list[Part] = Field(default_factory=list[Part])
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] | None = Field(default=None)
