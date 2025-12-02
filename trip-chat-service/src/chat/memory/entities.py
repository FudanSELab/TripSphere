from typing import Any

from pydantic import BaseModel, Field

from chat.common.parts import Part
from chat.utils.uuid import uuid7


class Memory(BaseModel):
    memory_id: str = Field(
        alias="_id",
        default_factory=lambda: str(uuid7()),
        examples=["019a3b16-4759-767c-bc8c-eb3e094c71b9"],
    )
    content: list[Part] = Field(default_factory=list[Part])
    metadata: dict[str, Any] | None = Field(default=None)
