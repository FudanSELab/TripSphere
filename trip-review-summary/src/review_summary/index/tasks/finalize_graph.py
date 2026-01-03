import logging
from typing import Any

import polars as pl
from asgiref.sync import async_to_sync
from celery import Task, shared_task
from neo4j import AsyncDriver, AsyncGraphDatabase

from review_summary.config.index.finalize_graph_config import FinalizeGraphConfig
from review_summary.config.settings import get_settings
from review_summary.utils.storage import get_storage_options
from review_summary.utils.uuid import uuid7

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_workflow(
    self: Task[Any, Any], context: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    async_to_sync(_finalize_graph)(
        self, context, FinalizeGraphConfig.model_validate(config)
    )
    return context


async def _finalize_graph(
    task: Task[Any, Any], context: dict[str, Any], config: FinalizeGraphConfig
) -> None:
    entities_filename = context["entities"]
    relationships_filename = context["relationships"]
    entities = pl.scan_parquet(
        f"s3://review-summary/{entities_filename}",
        storage_options=get_storage_options(),
    ).collect()
    relationships = pl.scan_parquet(
        f"s3://review-summary/{relationships_filename}",
        storage_options=get_storage_options(),
    ).collect()
    logger.info(
        f"Loaded entities from {entities_filename} and "
        f"relationships from {relationships_filename}."
    )

    finalized_entities = entities.with_columns(
        pl.Series("id", [uuid7() for _ in range(len(entities))]),
        pl.Series("readable_id", range(len(entities))),
    )
    finalized_relationships = relationships.with_columns(
        pl.Series("id", [uuid7() for _ in range(len(relationships))]),
        pl.Series("readable_id", range(len(relationships))),
    )

    settings = get_settings()
    neo4j_driver: AsyncDriver | None = None
    try:
        neo4j_driver = AsyncGraphDatabase.driver(  # pyright: ignore
            settings.neo4j.uri,
            auth=(
                settings.neo4j.username,
                settings.neo4j.password.get_secret_value(),
            ),
        )
        

    finally:
        if isinstance(neo4j_driver, AsyncDriver):
            await neo4j_driver.close()
