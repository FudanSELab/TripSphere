import logging

import polars as pl
from neo4j import AsyncDriver

logger = logging.getLogger(__name__)


async def create_graph(
    neo4j_driver: AsyncDriver,
    nodes: pl.LazyFrame,
    edges: pl.LazyFrame,
    attributes: dict[str, str],
) -> None:
    """Create a neo4j graph from nodes and edges dataframes."""
    if "target_id" not in attributes or "target_type" not in attributes:
        raise ValueError("Attributes must include 'target_id' and 'target_type' keys.")

    nodes_lookup = nodes.select(["id", "title"])
    edges = (
        edges.join(
            nodes_lookup.rename({"id": "source_id", "title": "source"}),
            on="source",
            how="left",
        )
        .join(
            nodes_lookup.rename({"id": "target_id", "title": "target"}),
            on="target",
            how="left",
        )
        .with_columns(
            pl.col("source_id").alias("source"), pl.col("target_id").alias("target")
        )
        .drop(["source_id", "target_id"])
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

        final_nodes = nodes.with_columns(
            pl.lit(attributes["target_id"]).alias("target_id"),
            pl.lit(attributes["target_type"]).alias("target_type"),
        ).collect()
        final_edges = edges.with_columns(
            pl.lit(attributes["target_id"]).alias("target_id"),
            pl.lit(attributes["target_type"]).alias("target_type"),
        ).collect()

        # Import finalized entities
        logger.info(f"Importing {len(final_nodes)} entities to Neo4j...")
        entities_dicts = final_nodes.to_dicts()
        result = await session.run(
            """
            UNWIND $entities AS entity
            MERGE (n:Entity {id: entity.id})
            SET n.readable_id = entity.readable_id,
                n.title = entity.title,
                n.type = entity.type,
                n.description = entity.description,
                n.frequency = entity.frequency,
                n.target_id = entity.target_id,
                n.target_type = entity.target_type
            """,
            entities=entities_dicts,
        )
        logger.debug(f"Entities import result: {result}")

        # Import finalized relationships
        logger.info(f"Importing {len(final_edges)} relationships to Neo4j...")
        relationships_dicts = final_edges.to_dicts()
        result = await session.run(
            """
            UNWIND $relationships AS rel
            MATCH (source:Entity {id: rel.source})
            MATCH (target:Entity {id: rel.target})
            MERGE (source)-[r:RELATES {id: rel.id}]->(target)
            SET r.readable_id = rel.readable_id,
                r.description = rel.description,
                r.weight = rel.weight,
                r.target_id = rel.target_id,
                r.target_type = rel.target_type
            """,
            relationships=relationships_dicts,
        )
        logger.debug(f"Relationships import result: {result}")

        logger.info("Imported entities and relationships to Neo4j")
