from typing import Any

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


class Document(Named):
    type: str = Field(default="text", description="Type of the document.")
    text_unit_ids: list[str] = Field(
        default_factory=list, description="List of text units in the document."
    )
    text: str = Field(default="", description="The raw text content of the review.")
    attributes: dict[str, Any] | None = Field(
        default=None,
        description="A dictionary of structured attributes such as author, etc.",
    )


class TextUnit(Identified):
    text: str = Field(..., description="The text of the unit.")
    embedding: list[float] | None = Field(
        default=None, description="The semantic (i.e. text) embedding of the text unit."
    )
    entity_ids: list[str] | None = Field(
        default=None, description="List of entity IDs related to the text unit."
    )
    relationship_ids: list[str] | None = Field(
        default=None, description="List of relationship IDs related to the text unit."
    )
    covariate_ids: dict[str, list[str]] | None = Field(
        default=None,
        description="Dict of different types of covariates related to the text unit.",
    )
    n_tokens: int | None = Field(
        default=None, description="The number of tokens in the text."
    )
    document_id: str | None = Field(
        default=None, description="The document ID in which the text unit appears."
    )
    attributes: dict[str, Any] | None = Field(
        default=None,
        description="A dict of additional attributes associated with the text unit.",
    )


class Entity(Named):
    type: str | None = Field(default=None)
    description: str | list[str] | None = Field(
        default=None, description="The description(s) of the entity."
    )
    description_embedding: list[float] | None = Field(
        default=None,
        description="The semantic (i.e. text) embedding of the description.",
    )
    name_embedding: list[float] | None = Field(
        default=None, description="The semantic (i.e. text) embedding of the entity."
    )
    community_ids: list[str] | None = Field(
        default=None, description="The community IDs of the entity."
    )
    text_unit_ids: list[str] | None = Field(
        default=None,
        description="List of text unit IDs in which the entity appears.",
    )
    rank: int | None = Field(
        default=1,
        description=(
            "Rank of the entity, used for sorting. "
            "Higher rank indicates more important entity."
        ),
    )
    attributes: dict[str, Any] | None = Field(
        default=None,
        description="A dictionary of structured attributes such as author, etc.",
    )


class Relationship(Identified):
    source: str = Field(..., description="The source entity name.")
    target: str = Field(..., description="The target entity name.")
    weight: float | None = Field(default=1.0, description="The edge weight.")
    description: str | list[str] | None = Field(
        default=None, description="The description(s) of the relationship."
    )
    description_embedding: list[float] | None = Field(
        default=None,
        description="The semantic embedding for the relationship description.",
    )
    text_unit_ids: list[str] | None = Field(
        default=None,
        description="List of text unit IDs in which the relationship appears.",
    )
    rank: int | None = Field(
        default=1,
        description=(
            "Rank of the relationship, used for sorting. "
            "Higher rank indicates more important relationship."
        ),
    )
    attributes: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Additional attributes associated with the relationship. "
            "To be included in the search prompt"
        ),
    )
