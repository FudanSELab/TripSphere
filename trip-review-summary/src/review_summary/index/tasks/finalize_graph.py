from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from celery import Task, shared_task
from graphdatascience import GraphDataScience
from neo4j import Driver, GraphDatabase

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
    _finalize_graph(self, context, FinalizeGraphConfig.model_validate(config))
    return context


def _finalize_graph(
    task: Task[Any, Any], context: dict[str, Any], config: FinalizeGraphConfig
) -> None:
    """Final `entities` parquet schema:
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
    Final `relationships` parquet schema:
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
    neo4j_driver = GraphDatabase.driver(  # pyright: ignore
        uri=settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password.get_secret_value()),
    )
    gds: GraphDataScience | None = None
    if config.embed_graph_enabled is True:
        gds = GraphDataScience.from_neo4j_driver(neo4j_driver)
        logger.debug(f"Graph Data Science client, version: {gds.version()}")

    try:
        _internal(task, context, config, neo4j_driver, gds)

    finally:
        if config.embed_graph_enabled and isinstance(gds, GraphDataScience):
            gds.close()
        neo4j_driver.close()  # Ensure the driver is closed properly


def _internal(
    task: Task[Any, Any],
    context: dict[str, Any],
    config: FinalizeGraphConfig,
    neo4j_driver: Driver,
    gds: GraphDataScience | None = None,
    checkpoint_id: str | None = None,
) -> None:
    entities_filename = context["entities"]
    relationships_filename = context["relationships"]
    entities = pd.read_parquet(  # pyright: ignore
        f"s3://review-summary/{entities_filename}",
        storage_options=get_storage_options(),
    )
    relationships = pd.read_parquet(  # pyright: ignore
        f"s3://review-summary/{relationships_filename}",
        storage_options=get_storage_options(),
    )
    logger.info(
        f"Loaded entities from {entities_filename} and "
        f"relationships from {relationships_filename}."
    )

    final_entities = entities.assign(
        id=[str(uuid7()) for _ in range(len(entities))],
        readable_id=pd.Series(range(len(entities))).astype(str),
    )[["id", "readable_id", *entities.columns]]
    final_relationships = relationships.assign(
        id=[str(uuid7()) for _ in range(len(relationships))],
        readable_id=pd.Series(range(len(relationships))).astype(str),
    )[["id", "readable_id", *relationships.columns]]

    msg = (
        f"Finalized {len(final_entities)} entities and "
        f"{len(final_relationships)} relationships."
    )
    logger.info(msg)
    task.update_state(state="PROGRESS", meta={"description": msg})

    create_graph(
        neo4j_driver=neo4j_driver,
        nodes=final_entities,
        edges=final_relationships,
        attributes={
            "target_id": context["target_id"],
            "target_type": context["target_type"],
        },
    )

    if config.embed_graph_enabled and isinstance(gds, GraphDataScience):
        raise NotImplementedError("Graph embedding is coming soon!")

    # Save entities and relationships to storage
    checkpoint_id = checkpoint_id or str(uuid7())
    entities_filename = f"entities_{checkpoint_id}.parquet"
    final_entities.to_parquet(
        f"s3://review-summary/{entities_filename}",
        storage_options=get_storage_options(),
    )
    relationships_filename = f"relationships_{checkpoint_id}.parquet"
    final_relationships.to_parquet(
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
