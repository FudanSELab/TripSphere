from __future__ import annotations

import logging
from typing import Any

import polars as pl
from asgiref.sync import async_to_sync
from celery import Task, shared_task
from neo4j import AsyncDriver, AsyncGraphDatabase

from review_summary.config.index.finalize_graph_config import FinalizeGraphConfig
from review_summary.config.settings import get_settings
from review_summary.index.operations.create_graph import create_graph
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
    """Final `entities` polars DataFrame schema:
    | Column        | Type         | Description                                          |
    | :------------ | :----------- | :--------------------------------------------------- |
    | id            | String       | ID of the Entity                                     |
    | readable_id   | String       | Human-friendly ID of the Entity                      |
    | title         | String       | Name of the Entity                                   |
    | type          | String       | Type of the Entity                                   |
    | description   | String       | Description of the Entity                            |
    | text_unit_ids | List(String) | IDs of TextUnits from which the Entity was extracted |
    | frequency     | UInt32       | Frequency of the Entity appearance in all TextUnits  |

    ---
    Final `relationships` polars DataFrame schema:
    | Column        | Type         | Description                                                |
    | :------------ | :----------- | :--------------------------------------------------------- |
    | id            | String       | ID of the Relationship                                     |
    | readable_id   | String       | Human-friendly ID of the Relationship                      |
    | source        | String       | Source Entity name of the Relationship                     |
    | target        | String       | Target Entity name of the Relationship                     |
    | description   | String       | Description of the Relationship                            |
    | text_unit_ids | List(String) | IDs of TextUnits from which the Relationship was extracted |
    | weight        | Float64      | Weight of the Relationship                                 |
    """  # noqa: E501
    settings = get_settings()
    neo4j_driver = AsyncGraphDatabase.driver(  # pyright: ignore
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password.get_secret_value()),
    )
    try:
        await _internal(task, context, config, neo4j_driver)

    finally:
        await neo4j_driver.close()  # Ensure the driver is closed properly


async def _internal(
    task: Task[Any, Any],
    context: dict[str, Any],
    config: FinalizeGraphConfig,
    neo4j_driver: AsyncDriver,
    checkpoint_id: str | None = None,
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

    final_entities = entities.with_columns(
        pl.Series("id", [str(uuid7()) for _ in range(len(entities))]),
        pl.Series("readable_id", range(len(entities))),
    ).select(["id", "readable_id", *entities.columns])
    final_relationships = relationships.with_columns(
        pl.Series("id", [str(uuid7()) for _ in range(len(relationships))]),
        pl.Series("readable_id", range(len(relationships))),
    ).select(["id", "readable_id", *relationships.columns])

    msg = (
        f"Finalized {len(final_entities)} entities and "
        f"{len(final_relationships)} relationships."
    )
    logger.info(msg)
    task.update_state(state="PROGRESS", meta={"description": msg})

    await create_graph(
        neo4j_driver=neo4j_driver,
        nodes=final_entities.lazy(),
        edges=final_relationships.lazy(),
        attributes={
            "target_id": context["target_id"],
            "target_type": context["target_type"],
        },
    )

    # Save entities and relationships to storage
    checkpoint_id = checkpoint_id or str(uuid7())
    entities_filename = f"entities_{checkpoint_id}.parquet"
    final_entities.write_parquet(
        f"s3://review-summary/{entities_filename}",
        storage_options=get_storage_options(),
    )
    relationships_filename = f"relationships_{checkpoint_id}.parquet"
    final_relationships.write_parquet(
        f"s3://review-summary/{relationships_filename}",
        storage_options=get_storage_options(),
    )

    # Update context with filenames
    context["entities"] = entities_filename
    context["relationships"] = relationships_filename
    logger.info(
        f"Saved finalized entities to {entities_filename} and "
        f"finalized relationships to {relationships_filename}."
    )
