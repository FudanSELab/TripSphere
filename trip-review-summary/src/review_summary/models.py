from typing import Any

from pydantic import BaseModel, Field

from review_summary.utils.uuid import uuid7


class Identified(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid7()),
        description="Unique identifier of the item.",
    )
    readable_id: str | None = Field(
        default=None,
        description="A human-friendly identifier for the item."
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
    title_embedding: list[float] | None = Field(
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


class CommunityReport(Named):
    """Defines an LLM-generated summary report of a community."""

    community_id: str
    """The ID of the community this report is associated with."""

    summary: str = ""
    """Summary of the report."""

    full_content: str = ""
    """Full content of the report."""

    rank: float | None = 1.0
    """Rank of the report, used for sorting (optional). Higher means more important"""

    full_content_embedding: list[float] | None = None
    """The semantic (i.e. text) embedding of the full report content (optional)."""

    attributes: dict[str, Any] | None = None
    """A dictionary of additional attributes associated with the report (optional)."""

    size: int | None = None
    """The size of the report (Amount of text units)."""

    period: str | None = None
    """The period of the report (optional)."""

    def from_dict(
        self,
        d: dict[str, Any],
        id_key: str = "id",
        title_key: str = "title",
        community_id_key: str = "community",
        short_id_key: str = "human_readable_id",
        summary_key: str = "summary",
        full_content_key: str = "full_content",
        rank_key: str = "rank",
        attributes_key: str = "attributes",
        size_key: str = "size",
        period_key: str = "period",
    ) -> "CommunityReport":
        """Create a new community report from the dict data."""
        return CommunityReport(
            id=d[id_key],
            title=d[title_key],
            community_id=d[community_id_key],
            readable_id=d.get(short_id_key),
            summary=d[summary_key],
            full_content=d[full_content_key],
            rank=d[rank_key],
            attributes=d.get(attributes_key),
            size=d.get(size_key),
            period=d.get(period_key),
        )


class Covariate(Identified):
    """
    A protocol for a covariate in the system.

    Covariates are metadata associated with a subject, e.g. entity claims.
    Each subject (e.g. entity) may be associated with multiple types of covariates.
    """

    subject_id: str
    """The subject id."""

    subject_type: str = "entity"
    """The subject type."""

    covariate_type: str = "claim"
    """The covariate type."""

    text_unit_ids: list[str] | None = None
    """List of text unit IDs in which the covariate info appears (optional)."""

    attributes: dict[str, Any] | None = None

    def from_dict(
        self,
        d: dict[str, Any],
        id_key: str = "id",
        subject_id_key: str = "subject_id",
        covariate_type_key: str = "covariate_type",
        short_id_key: str = "human_readable_id",
        text_unit_ids_key: str = "text_unit_ids",
        attributes_key: str = "attributes",
    ) -> "Covariate":
        """Create a new covariate from the dict data."""
        return Covariate(
            id=d[id_key],
            readable_id=d.get(short_id_key),
            subject_id=d[subject_id_key],
            covariate_type=d.get(covariate_type_key, "claim"),
            text_unit_ids=d.get(text_unit_ids_key),
            attributes=d.get(attributes_key),
        )
