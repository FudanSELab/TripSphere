import logging

import pandas as pd
from neo4j import Driver

logger = logging.getLogger(__name__)


def create_graph(
    neo4j_driver: Driver,
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    attributes: dict[str, str],
) -> None:
    """Create a neo4j graph from nodes and edges DataFrames."""
    if "target_id" not in attributes or "target_type" not in attributes:
        raise ValueError("Attributes must include 'target_id' and 'target_type' keys.")

    # Create mapping from title to id
    title_to_id = nodes.set_index("title")["id"]

    # Map source and target titles to their IDs
    edges["source"] = edges["source"].map(title_to_id)
    edges["target"] = edges["target"].map(title_to_id)

    with neo4j_driver.session() as session:  # pyright: ignore
        # Create indexes to optimize queries by target_id
        session.run(
            "CREATE INDEX entity_target_id "
            "IF NOT EXISTS FOR (n:Entity) ON (n.target_id)"
        )
        session.run(
            "CREATE INDEX relationship_target_id "
            "IF NOT EXISTS FOR ()-[r:RELATES]-() ON (r.target_id)"
        )

        # Add attributes using assign for better performance
        final_nodes = nodes.assign(**attributes)
        final_edges = edges.assign(**attributes)

        # Import finalized entities
        logger.info(f"Importing {len(final_nodes)} entities to Neo4j...")
        entities_dicts = final_nodes.to_dict("records")  # pyright: ignore
        result = session.run(
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
        relationships_dicts = final_edges.to_dict("records")  # pyright: ignore
        result = session.run(
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
