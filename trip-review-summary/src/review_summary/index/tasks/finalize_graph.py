import logging
from typing import Any, cast

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
    target_id = cast(str, context["target_id"])
    target_type = cast(str, context["target_type"])

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
        pl.lit(target_id).alias("target_id"),
        pl.lit(target_type).alias("target_type"),
    )
    finalized_relationships = relationships.with_columns(
        pl.Series("id", [uuid7() for _ in range(len(relationships))]),
        pl.Series("readable_id", range(len(relationships))),
        pl.lit(target_id).alias("target_id"),
        pl.lit(target_type).alias("target_type"),
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

        async with neo4j_driver.session() as session:  # pyright: ignore
            # Create indexes to optimize queries by target_id
            await session.run(
                "CREATE INDEX entity_target_id "
                "IF NOT EXISTS FOR (n:Entity) ON (n.target_id)"
            )
            await session.run(
                "CREATE INDEX relationship_target_id "
                "IF NOT EXISTS FOR ()-[r:RELATES]-() ON (r.target_id)"
            )

            # Import finalized entities
            logger.info(f"Importing {len(finalized_entities)} entities to Neo4j...")
            entities_dicts = finalized_entities.to_dicts()
            await session.run(
                """
                UNWIND $entities AS entity
                MERGE (n:Entity {id: entity.id})
                SET n.readable_id = entity.readable_id,
                    n.target_id = entity.target_id,
                    n.target_type = entity.target_type,
                    n.name = entity.name,
                    n.type = entity.type,
                    n.description = entity.description
                """,
                entities=entities_dicts,
            )

            # Import finalized relationships
            logger.info(
                f"Importing {len(finalized_relationships)} relationships to Neo4j..."
            )
            relationships_dicts = finalized_relationships.to_dicts()
            await session.run(
                """
                UNWIND $relationships AS rel
                MATCH (source:Entity {id: rel.source})
                MATCH (target:Entity {id: rel.target})
                MERGE (source)-[r:RELATES {id: rel.id}]->(target)
                SET r.readable_id = rel.readable_id,
                    r.target_id = rel.target_id,
                    r.target_type = rel.target_type,
                    r.type = rel.type,
                    r.description = rel.description,
                    r.weight = rel.weight
                """,
                relationships=relationships_dicts,
            )

            logger.info("Successfully imported entities and relationships to Neo4j")

    finally:
        if isinstance(neo4j_driver, AsyncDriver):
            await neo4j_driver.close()
