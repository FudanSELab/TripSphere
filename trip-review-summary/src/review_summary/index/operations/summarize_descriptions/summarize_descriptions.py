import asyncio
import logging
from typing import Any

import pandas as pd
from langchain_openai import ChatOpenAI

from review_summary.config.settings import get_settings
from review_summary.index.operations.summarize_descriptions.summary_extractor import (
    SummaryExtractor,
)
from review_summary.index.operations.summarize_descriptions.typing import (
    SummarizationResult,
)

logger = logging.getLogger(__name__)


async def summarize_descriptions(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
    chat_model_config: dict[str, Any],
    max_input_tokens: int,
    max_summary_length: int,
    summarization_prompt: str | None = None,
    num_concurrency: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize entity and relationship descriptions using a llm."""
    semaphore = asyncio.Semaphore(num_concurrency)

    # Initialize ChatOpenAI model with provided config
    openai_settings = get_settings().openai
    if "api_key" not in chat_model_config:
        chat_model_config["api_key"] = openai_settings.api_key
    if "base_url" not in chat_model_config:
        chat_model_config["base_url"] = openai_settings.base_url
    chat_model = ChatOpenAI(**chat_model_config)
    logger.info("Initialized ChatOpenAI model for description summarization.")

    async def _summarize_descriptions(
        id: str | tuple[str, str], descriptions: list[str]
    ) -> SummarizationResult:
        async with semaphore:
            return await _run_summary_extraction(
                id=id,
                descriptions=descriptions,
                chat_model=chat_model,
                max_input_tokens=max_input_tokens,
                max_summary_length=max_summary_length,
                summarization_prompt=summarization_prompt,
            )

    # Process entities
    entity_futures = [
        _summarize_descriptions(str(row.title), sorted(set(row.description)))  # type: ignore
        for row in entities.itertuples()
    ]
    logger.info("Starting summarization of entity descriptions.")
    entity_results = await asyncio.gather(*entity_futures)

    # Process relationships
    relationship_futures = [
        _summarize_descriptions(
            (str(row.source), str(row.target)),  # ty: ignore
            sorted(set(row.description)),  # type: ignore
        )
        for row in relationships.itertuples()
    ]
    logger.info("Starting summarization of relationship descriptions.")
    relationship_results = await asyncio.gather(*relationship_futures)

    # Build DataFrames using Polars-native construction
    entity_descriptions = pd.DataFrame(
        {
            "title": [result.id for result in entity_results],
            "description": [result.description for result in entity_results],
        }
    )
    relationship_descriptions = pd.DataFrame(
        {
            "source": [result.id[0] for result in relationship_results],
            "target": [result.id[1] for result in relationship_results],
            "description": [result.description for result in relationship_results],
        }
    )

    return entity_descriptions, relationship_descriptions


async def _run_summary_extraction(
    id: str | tuple[str, str],
    descriptions: list[str],
    chat_model: ChatOpenAI,
    max_input_tokens: int,
    max_summary_length: int,
    summarization_prompt: str | None = None,
) -> SummarizationResult:
    extractor = SummaryExtractor(
        chat_model=chat_model,
        summarization_prompt=summarization_prompt,
        max_summary_length=max_summary_length,
        max_input_tokens=max_input_tokens,
    )

    result = await extractor(id=id, descriptions=descriptions)
    return SummarizationResult(id=result.id, description=result.description)
