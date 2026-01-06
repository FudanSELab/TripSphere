"""Integration tests for EntityVectorStore."""

from pathlib import Path

import pandas as pd
import pytest
import pytest_asyncio
from qdrant_client import AsyncQdrantClient

from review_summary.models import Entity
from review_summary.vector_stores.entity import EntityVectorStore


@pytest_asyncio.fixture
async def qdrant_client() -> AsyncQdrantClient:
    """Create an in-memory Qdrant client for testing."""
    client = AsyncQdrantClient(":memory:")
    return client


@pytest_asyncio.fixture
async def vector_store(qdrant_client: AsyncQdrantClient) -> EntityVectorStore:
    """Create an EntityVectorStore with in-memory client."""
    return await EntityVectorStore.create_vector_store(
        client=qdrant_client, vector_dim=3072
    )


@pytest.fixture
def entities() -> list[Entity]:
    """Load entities from fixtures file."""
    fixtures_path = Path("tests") / "fixtures" / "entities.parquet"
    df = pd.read_parquet(fixtures_path, dtype_backend="pyarrow")
    return [Entity.model_validate(entity.to_dict()) for _, entity in df.iterrows()]


@pytest.mark.asyncio
async def test_save_multiple_success(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test saving multiple entities to the vector store."""
    # Save entities
    await vector_store.save_multiple(entities)

    # Verify by searching for them
    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    # Search should return results
    results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=10,
    )

    # Should have results
    assert len(results) > 0


@pytest.mark.asyncio
async def test_save_multiple_empty_list(vector_store: EntityVectorStore) -> None:
    """Test that saving empty list doesn't raise error."""
    # Should not raise any exception
    await vector_store.save_multiple([])


@pytest.mark.asyncio
async def test_save_multiple_preserves_attributes(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test that attributes are preserved when saving entities."""
    # Save entities
    await vector_store.save_multiple(entities)

    # Search and verify
    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=1,
    )

    assert len(results) > 0
    retrieved_entity = results[0]

    # Find matching original entity by title
    original_entity = next(
        entity for entity in entities if entity.title == retrieved_entity.title
    )

    # Verify attributes are preserved
    assert retrieved_entity.attributes == original_entity.attributes
    assert retrieved_entity.title == original_entity.title
    assert retrieved_entity.type == original_entity.type


@pytest.mark.asyncio
async def test_search_by_vector_success(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test searching entities by embedding vector."""
    # Save entities first
    await vector_store.save_multiple(entities)

    # Use the first entity's description embedding for search
    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    # Search by vector
    target_id = "attraction-001"
    target_type = "attraction"
    results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id=target_id,
        target_type=target_type,
        top_k=5,
    )

    # Should return results
    assert len(results) > 0
    assert len(results) <= 5

    # The first result should be the same entity (highest similarity)
    assert results[0].title == entities[0].title

    # All results should have the correct target
    for entity in results:
        assert entity.attributes is not None
        assert entity.attributes["target_id"] == target_id
        assert entity.attributes["target_type"] == target_type


@pytest.mark.asyncio
async def test_search_by_vector_respects_top_k(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test that search_by_vector respects the top_k parameter."""
    # Save entities
    await vector_store.save_multiple(entities)

    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    # Test different top_k values
    for top_k in [1, 3, 5, 10]:
        results = await vector_store.search_by_vector(
            embedding_vector=query_embedding,
            target_id="attraction-001",
            target_type="attraction",
            top_k=top_k,
        )

        # Should return at most top_k results
        assert len(results) <= top_k


@pytest.mark.asyncio
async def test_search_by_vector_filters_by_target(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test that search_by_vector correctly filters by target_id and target_type."""
    # Modify some entities to have different targets
    modified_entities = entities.copy()
    for entity in modified_entities[:3]:
        if entity.attributes:
            entity.attributes["target_id"] = "hotel-001"
            entity.attributes["target_type"] = "hotel"

    # Save all entities
    await vector_store.save_multiple(modified_entities)

    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    # Search for attraction entities only
    attraction_results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=1024,
    )

    # Should only return attraction entities
    assert len(attraction_results) == len(entities) - 3
    for entity in attraction_results:
        assert entity.attributes is not None
        assert entity.attributes["target_id"] == "attraction-001"
        assert entity.attributes["target_type"] == "attraction"

    # Search for hotel entities only
    hotel_results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="hotel-001",
        target_type="hotel",
        top_k=10,
    )

    # Should only return hotel entities
    assert len(hotel_results) == 3
    for entity in hotel_results:
        assert entity.attributes is not None
        assert entity.attributes["target_id"] == "hotel-001"
        assert entity.attributes["target_type"] == "hotel"


@pytest.mark.asyncio
async def test_search_by_vector_empty_results(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test search_by_vector with no matching results."""
    # Save entities
    await vector_store.save_multiple(entities)

    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    # Search for non-existent target
    results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="nonexistent-id",
        target_type="attraction",
        top_k=10,
    )

    # Should return empty list
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_by_vector_ordering(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test that search results are ordered by similarity (score)."""
    # Save entities
    await vector_store.save_multiple(entities)

    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    # Search by vector
    results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=10,
    )

    # Results should be ordered by similarity
    # The first result should be the queried entity itself (highest similarity)
    assert len(results) > 1
    assert results[0].title == entities[0].title


@pytest.mark.asyncio
async def test_search_by_vector_no_embeddings_in_results(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test that search results don't include embeddings."""
    # Save entities with embeddings
    await vector_store.save_multiple(entities)

    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    # Search by vector
    results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=5,
    )

    # Results should not include embeddings
    for entity in results:
        assert entity.description_embedding is None
        assert entity.title_embedding is None


@pytest.mark.asyncio
async def test_save_multiple_upsert_behavior(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test that save_multiple performs upsert (update or insert)."""
    # Save entities first time
    await vector_store.save_multiple(entities)

    # Modify the entities
    modified_entities = entities.copy()
    for entity in modified_entities:
        if isinstance(entity.description, str):
            entity.description = "MODIFIED: " + entity.description
        else:
            entity.description = "MODIFIED: description"

    # Save again with same IDs
    await vector_store.save_multiple(modified_entities)

    # Search and verify update
    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=1024,
    )

    # Should still have same number of entities (upsert, not duplicate)
    assert len(results) == len(entities)

    # Verify descriptions are modified
    for entity in results:
        if isinstance(entity.description, str):
            assert entity.description.startswith("MODIFIED:")


@pytest.mark.asyncio
async def test_search_by_vector_mixed_targets(
    vector_store: EntityVectorStore, entities: list[Entity]
) -> None:
    """Test search across different target types."""
    # Create entities with different target types
    attraction_entities = entities[:5].copy()
    hotel_entities = entities[5:].copy()

    for entity in hotel_entities:
        if entity.attributes:
            entity.attributes["target_id"] = "hotel-001"
            entity.attributes["target_type"] = "hotel"

    # Save all entities
    await vector_store.save_multiple(attraction_entities + hotel_entities)

    query_embedding = entities[0].description_embedding
    assert query_embedding is not None

    # Search for attractions
    attraction_results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=10,
    )

    # Search for hotels
    hotel_results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="hotel-001",
        target_type="hotel",
        top_k=10,
    )

    # Verify no overlap
    attraction_ids = {e.id for e in attraction_results}
    hotel_ids = {e.id for e in hotel_results}
    assert len(attraction_ids & hotel_ids) == 0

    # Verify counts
    assert len(attraction_results) <= 5
    assert len(hotel_results) == min(10, len(entities) - 5)
