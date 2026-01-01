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
    target_id = cast(str, context["target_id"])
    target_type = cast(str, context["target_type"])
    if target_type != "attraction":
        # Currently, we only support attraction reviews
        raise ValueError(f"Unsupported target type: {target_type}")
    qdrant_client: AsyncQdrantClient | None = None
    try:
        qdrant_client = AsyncQdrantClient(url=get_settings().qdrant.url)
        text_unit_vector_store = await TextUnitVectorStore.create_vector_store(
            client=qdrant_client, vector_dim=3072
        )
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
        logger.info(f"Saved collected text units to 's3://review-summary/{filename}'.")
    finally:
        if qdrant_client is not None:
            await qdrant_client.close()


if __name__ == "__main__":
    # For local testing
    test_context = {
        "target_id": "attraction_12345",
        "target_type": "attraction",
    }
    result = run_workflow.apply(args=(test_context,))
    print("Final context:", result.result)
