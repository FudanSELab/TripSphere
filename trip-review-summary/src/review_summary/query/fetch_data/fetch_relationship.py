from neo4j import AsyncDriver

from review_summary.models import Entity, Relationship


async def fetch_relationships_for_entities(
    driver: AsyncDriver, entities: list[Entity]
) -> list[Relationship]:
    if not entities:
        return []

    entity_ids = [e.id for e in entities]

    query = """
    MATCH (a:Entity)-[r]->(b:Entity)
    WHERE a.id IN $entity_ids OR b.id IN $entity_ids
    RETURN 
        r.id AS id,
        r.readable_id AS readable_id,
        a.title AS source,
        b.title AS target,
        r.weight AS weight,
        r.description AS description,
        r.target_id AS target_id,
        r.target_type AS target_type
    """

    async with driver.session() as session:  # pyright: ignore
        result = await session.run(query, entity_ids=entity_ids)
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
                }
                or None,
            }
            relationships_data.append(Relationship.model_validate(rel_dict))
        return relationships_data
