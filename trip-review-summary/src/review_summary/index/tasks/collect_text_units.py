from __future__ import annotations

import logging
from typing import Any, cast

import polars as pl
from asgiref.sync import async_to_sync
from celery import Task, shared_task
from qdrant_client import AsyncQdrantClient

from review_summary.config.settings import get_settings
from review_summary.utils.storage import get_storage_options
from review_summary.utils.uuid import uuid7
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_workflow(self: Task[Any, Any], context: dict[str, Any]) -> dict[str, Any]:
    async_to_sync(_collect_text_units)(self, context)
    return context


async def _collect_text_units(task: Task[Any, Any], context: dict[str, Any]) -> None:
    qdrant_settings = get_settings().qdrant
    qdrant_client = AsyncQdrantClient(url=qdrant_settings.url)
    try:
        text_unit_vector_store = await TextUnitVectorStore.create_vector_store(
            client=qdrant_client, vector_dim=context.get("vector_dim", 3072)
        )
        await _internal(task, context, text_unit_vector_store)

    finally:
        await qdrant_client.close()  # Ensure the client is closed properly


async def _internal(
    task: Task[Any, Any],
    context: dict[str, Any],
    text_unit_vector_store: TextUnitVectorStore,
) -> None:
    target_id = cast(str, context["target_id"])
    target_type = cast(str, context["target_type"])
    if target_type != "attraction":
        # Currently, we only support attraction reviews
        raise ValueError(f"Unsupported target type: {target_type}")

    text_units = await text_unit_vector_store.find_by_target(target_id, target_type)

    msg = f"Collected {len(text_units)} text units for {target_type} {target_id}."
    logger.info(msg)
    task.update_state(
        state="PROGRESS",
        meta={
            "description": msg,
            "target_id": target_id,
            "target_type": target_type,
            "collected_text_units": len(text_units),
        },
    )

    df = pl.DataFrame([text_unit.model_dump() for text_unit in text_units])
    filename = f"text_units_{uuid7()}.parquet"
    df.write_parquet(
        f"s3://review-summary/{filename}", storage_options=get_storage_options()
    )
    context["text_units"] = filename
    logger.info(f"Saved text units to 's3://review-summary/{filename}'.")
