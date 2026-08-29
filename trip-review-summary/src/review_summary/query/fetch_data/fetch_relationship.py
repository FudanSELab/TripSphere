from neo4j import AsyncDriver

from review_summary.models import Entity, Relationship


async def fetch_relationships_for_entities(
    driver: AsyncDriver,
    entities: list[Entity],
    target_id: str,
    target_type: str,
    review_snapshot: str,
) -> list[Relationship]:
    if not entities:
        return []

    entity_ids = [e.id for e in entities]

    query = """
    MATCH (a:Entity)-[r]->(b:Entity)
    WHERE (a.id IN $entity_ids OR b.id IN $entity_ids)
      AND r.target_id = $target_id
      AND r.target_type = $target_type
      AND r.review_snapshot = $review_snapshot
    RETURN 
        r.id AS id,
        r.readable_id AS readable_id,
        a.title AS source,
        b.title AS target,
        r.weight AS weight,
        r.description AS description,
        r.target_id AS target_id,
        r.target_type AS target_type,
        r.review_snapshot AS review_snapshot
    """

    async with driver.session() as session:  # pyright: ignore
        result = await session.run(
            query,
            entity_ids=entity_ids,
            target_id=target_id,
            target_type=target_type,
            review_snapshot=review_snapshot,
        )
        relationships_data: list[Relationship] = []

        async for record in result:
            rel_dict = {
                "id": record["id"],
                "readable_id": record["readable_id"],
                "source": record["source"],
                "target": record["target"],
                "weight": record["weight"],
                "description": record["description"],
                "attributes": {
                    "target_id": record["target_id"],
                    "target_type": record["target_type"],
                    "review_snapshot": record["review_snapshot"],
                }
                or None,
            }
            relationships_data.append(Relationship.model_validate(rel_dict))
        return relationships_data
