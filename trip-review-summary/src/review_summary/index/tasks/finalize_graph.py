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
    """Final `entities` pyarrow schema:
    | Column        | Type         | Description                                          |
    | :------------ | :----------- | :--------------------------------------------------- |
    | id            | string       | ID of the Entity                                     |
    | readable_id   | string       | Human-friendly ID of the Entity                      |
    | title         | string       | Name of the Entity                                   |
    | type          | string       | Type of the Entity                                   |
    | description   | string       | Description of the Entity                            |
    | text_unit_ids | list<string> | IDs of TextUnits from which the Entity was extracted |
    | frequency     | int64        | Frequency of the Entity appearance in all TextUnits  |

    ---
    Final `relationships` pyarrow schema:
    | Column        | Type         | Description                                                |
    | :------------ | :----------- | :--------------------------------------------------------- |
    | id            | string       | ID of the Relationship                                     |
    | readable_id   | string       | Human-friendly ID of the Relationship                      |
    | source        | string       | Source Entity name of the Relationship                     |
    | target        | string       | Target Entity name of the Relationship                     |
    | description   | string       | Description of the Relationship                            |
    | text_unit_ids | list<string> | IDs of TextUnits from which the Relationship was extracted |
    | weight        | double       | Weight of the Relationship                                 |
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
    entities = pd.read_parquet(
        f"s3://review-summary/{entities_filename}",
        storage_options=get_storage_options(),
        dtype_backend="pyarrow",
    )
    relationships = pd.read_parquet(
        f"s3://review-summary/{relationships_filename}",
        storage_options=get_storage_options(),
        dtype_backend="pyarrow",
    )
    logger.info(
        f"Loaded entities from {entities_filename} and "
        f"relationships from {relationships_filename}."
    )

    # Finalize entities
    final_entities = entities.drop_duplicates(subset="title")
    final_entities = final_entities.loc[entities["title"].notna()].reset_index()
    final_entities = final_entities.assign(
        id=[str(uuid7()) for _ in range(len(final_entities))],
        readable_id=final_entities.index.astype(str),
    )[["id", "readable_id", *entities.columns]]

    # Finalize relationships
    final_relationships = relationships.drop_duplicates(subset=["source", "target"])
    final_relationships.reset_index(inplace=True)
    final_relationships = final_relationships.assign(
        id=[str(uuid7()) for _ in range(len(final_relationships))],
        readable_id=final_relationships.index.astype(str),
    )[["id", "readable_id", *relationships.columns]]

    message = (
        f"Finalized {len(final_entities)} entities and "
        f"{len(final_relationships)} relationships."
    )
    logger.info(message)
    task.update_state(state="PROGRESS", meta={"description": message})

    logger.info("Importing nodes and edges into Neo4j database.")
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
