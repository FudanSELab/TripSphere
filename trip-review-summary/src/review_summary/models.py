from typing import Any, Literal

from pydantic import BaseModel, Field

from review_summary.utils.uuid import uuid7


class Identified(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid7()),
        description="Unique identifier of the item.",
    )
    short_id: str | None = Field(
        default=None,
        description="A shorter, human-friendly identifier for the item."
        "Useful for referring to community in prompts or texts displayed to users, "
        "such as in a report text.",
    )


class Named(Identified):
    title: str = Field(..., description="The name/title of the item.")


class ReviewDocument(Named):
    type: Literal["text"] = Field(default="text", description="Type of the document.")
    text: str = Field(default="", description="The raw text content of the review.")
    attributes: dict[str, Any] | None = Field(
        default=None,
        description="A dictionary of structured attributes such as author, etc.",
    )


class Entity(Named): ...


class Relationship(Identified): ...
