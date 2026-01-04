import logging
from typing import Any

import polars as pl
from asgiref.sync import async_to_sync
from celery import Task, shared_task

from review_summary.config.index.extract_graph_config import ExtractGraphConfig
from review_summary.index.operations.extract_graph import extract_graph
from review_summary.index.operations.summarize_descriptions import (
    summarize_descriptions,
)
from review_summary.utils.storage import get_storage_options
from review_summary.utils.uuid import uuid7

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_workflow(
    self: Task[Any, Any], context: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    async_to_sync(_extract_graph)(
        self, context, ExtractGraphConfig.model_validate(config)
    )
    return context


async def _extract_graph(
    task: Task[Any, Any], context: dict[str, Any], config: ExtractGraphConfig
) -> None:
    # Load text units DataFrame from storage
    text_units_filename = context["text_units"]
    text_units = pl.scan_parquet(
        f"s3://review-summary/{text_units_filename}",
        storage_options=get_storage_options(),
    )
    logger.info(f"Loaded text units from {text_units_filename}.")

    extracted_entities, extracted_relationships = await extract_graph(
        text_units=text_units,
        text_column="text",
        id_column="id",
        entity_types=config.entity_types,
        chat_model_config=config.graph_llm_config,
        max_gleanings=config.max_gleanings,
        num_concurrency=config.graph_num_concurrency,
    )

    if len(extracted_entities) == 0:
        error_msg = "No entities detected during extraction."
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Extracted {len(extracted_entities)} raw entities.")

    if len(extracted_relationships) == 0:
        error_msg = "No relationships detected during extraction."
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Extracted {len(extracted_relationships)} raw relationships.")

    task.update_state(
        state="PROGRESS",
        meta={
            "description": "Graph extraction completed.",
            "extracted_entities": len(extracted_entities),
            "extracted_relationships": len(extracted_relationships),
        },
    )

    entity_summaries, relationship_summaries = await summarize_descriptions(
        entities=extracted_entities.lazy(),
        relationships=extracted_relationships.lazy(),
        chat_model_config=config.summary_llm_config,
        max_input_tokens=config.max_input_tokens,
        max_summary_length=config.max_length,
        num_concurrency=config.summary_num_concurrency,
    )

    relationships = extracted_relationships.drop("description").join(
        relationship_summaries, on=["source", "target"], how="left"
    )

    extracted_entities = extracted_entities.drop("description")
    entities = extracted_entities.join(entity_summaries, on="title", how="left")

    # Save entities and relationships to storage
    entities_filename = f"entities_{uuid7()}.parquet"
    entities.write_parquet(
        f"s3://review-summary/{entities_filename}",
        storage_options=get_storage_options(),
    )
    relationships_filename = f"relationships_{uuid7()}.parquet"
    relationships.write_parquet(
        f"s3://review-summary/{relationships_filename}",
        storage_options=get_storage_options(),
    )

    # Update context with filenames
    context["entities"] = entities_filename
    context["relationships"] = relationships_filename
    logger.info(
        f"Saved entities to {entities_filename} and "
        f"relationships to {relationships_filename}."
    )
