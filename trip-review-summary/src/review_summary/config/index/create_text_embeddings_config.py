from typing import Any

from pydantic import BaseModel, Field


class CreateTextEmbeddingsConfig(BaseModel):
    """Configuration for create_text_embeddings task."""

    embedding_llm_config: dict[str, Any] = Field(
        ..., description="The OpenAIEmbeddings configuration for text embeddings."
    )
    batch_size: int = Field(default=16, description="The batch size to use.")
    batch_max_tokens: int = Field(
        default=8191, description="The batch max tokens to use."
    )
    fields_to_embed: dict[str, list[str]] = Field(
        default={"entities": ["description"]},
        description="The fields to create text embeddings for.",
        examples=[{"dataframe_name": ["column_0", "column_1"]}],
    )
