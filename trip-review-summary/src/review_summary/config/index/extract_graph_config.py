from typing import Any

from pydantic import BaseModel, Field


class ExtractGraphConfig(BaseModel):
    """Configuration for extract_graph task."""

    # For extract_graph operation
    graph_llm_config: dict[str, Any] = Field(
        ..., description="The ChatOpenAI configuration for graph extraction."
    )
    entity_types: list[str] = Field(
        default=["POI", "product", "amenity", "constraint", "character"],
        description="The entity extraction entity types to use.",
    )
    max_gleanings: int = Field(
        default=1,
        description="The maximum number of entity gleanings to use.",
    )
    graph_num_concurrency: int = Field(
        default=4,
        description="The number of coroutines used for parallel processing.",
    )

    # For summarize_descriptions operation
    summary_llm_config: dict[str, Any] = Field(
        ..., description="The ChatOpenAI configuration for description summarization."
    )
    max_length: int = Field(
        default=500,
        description="The description summarization maximum length.",
    )
    max_input_tokens: int = Field(
        default=4000,
        description="Maximum tokens to submit from the input entity descriptions.",
    )
    summary_num_concurrency: int = Field(
        default=4,
        description="The number of coroutines used for parallel processing.",
    )
