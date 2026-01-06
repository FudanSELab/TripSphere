"""Integration tests for TextUnitVectorStore."""

import json
from pathlib import Path

import pytest
import pytest_asyncio
from qdrant_client import AsyncQdrantClient

from review_summary.models import TextUnit
from review_summary.vector_stores.text_unit import TextUnitVectorStore


@pytest_asyncio.fixture
async def qdrant_client() -> AsyncQdrantClient:
    """Create an in-memory Qdrant client for testing."""
    client = AsyncQdrantClient(":memory:")
    return client


@pytest_asyncio.fixture
async def vector_store(qdrant_client: AsyncQdrantClient) -> TextUnitVectorStore:
    """Create a TextUnitVectorStore with in-memory client."""
    return await TextUnitVectorStore.create_vector_store(
        client=qdrant_client, vector_dim=3072
    )


@pytest.fixture
def text_units() -> list[TextUnit]:
    """Load text units from fixtures file."""
    fixtures_path = Path("tests") / "fixtures" / "text_units.json"
    with open(fixtures_path, "r", encoding="utf-8") as f:
        text_units_data = json.load(f)
    # Load first 10 text units for testing
    return [TextUnit.model_validate(unit) for unit in text_units_data[:10]]


@pytest.mark.asyncio
async def test_save_multiple_success(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test saving multiple text units to the vector store."""
    # Save text units
    await vector_store.save_multiple(text_units)

    # Verify by searching for them
    target_id = (
        text_units[0].attributes["target_id"] if text_units[0].attributes else ""
    )
    target_type = (
        text_units[0].attributes["target_type"] if text_units[0].attributes else ""
    )

    # Retrieve saved text units
    retrieved = await vector_store.find_by_target(
        target_id=target_id, target_type=target_type, limit=100
    )

    # Verify all text units were saved
    assert len(retrieved) == len(text_units)

    # Verify text content matches (order may differ)
    retrieved_texts = {unit.text for unit in retrieved}
    original_texts = {unit.text for unit in text_units}
    assert retrieved_texts == original_texts


@pytest.mark.asyncio
async def test_save_multiple_empty_list(vector_store: TextUnitVectorStore) -> None:
    """Test that saving empty list doesn't raise error."""
    # Should not raise any exception
    await vector_store.save_multiple([])


@pytest.mark.asyncio
async def test_save_multiple_preserves_attributes(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test that attributes are preserved when saving text units."""
    # Save text units
    await vector_store.save_multiple(text_units)

    # Retrieve the first text unit
    target_id = (
        text_units[0].attributes["target_id"] if text_units[0].attributes else ""
    )
    target_type = (
        text_units[0].attributes["target_type"] if text_units[0].attributes else ""
    )
    retrieved = await vector_store.find_by_target(
        target_id=target_id, target_type=target_type, limit=1
    )

    assert len(retrieved) > 0
    retrieved_unit = retrieved[0]

    # Find matching original unit by text
    original_unit = next(
        unit for unit in text_units if unit.text == retrieved_unit.text
    )

    # Verify attributes are preserved
    assert retrieved_unit.attributes == original_unit.attributes
    assert retrieved_unit.readable_id == original_unit.readable_id
    assert retrieved_unit.n_tokens == original_unit.n_tokens


@pytest.mark.asyncio
async def test_find_by_target_success(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test finding text units by target ID and type."""
    # Save text units first
    await vector_store.save_multiple(text_units)

    # Find text units by target
    target_id = "attraction-001"
    target_type = "attraction"
    found_units = await vector_store.find_by_target(
        target_id=target_id, target_type=target_type
    )

    # All fixture text units should have the same target
    assert len(found_units) == len(text_units)

    # Verify all found units have correct target
    for unit in found_units:
        assert unit.attributes is not None
        assert unit.attributes["target_id"] == target_id
        assert unit.attributes["target_type"] == target_type
    # Make sure ids match original
    found_ids = {unit.id for unit in found_units}
    original_ids = {unit.id for unit in text_units}
    assert found_ids == original_ids


@pytest.mark.asyncio
async def test_find_by_target_no_results(vector_store: TextUnitVectorStore) -> None:
    """Test finding text units with no matching results."""
    # Try to find units that don't exist
    found_units = await vector_store.find_by_target(
        target_id="nonexistent-id", target_type="attraction"
    )

    # Should return empty list
    assert len(found_units) == 0


@pytest.mark.asyncio
async def test_find_by_target_filters_correctly(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test that find_by_target filters by both target_id and target_type."""
    # Modify some text units to have different targets
    modified_units = text_units.copy()
    for unit in modified_units[:3]:
        if unit.attributes:
            unit.attributes["target_id"] = "hotel-001"
            unit.attributes["target_type"] = "hotel"

    # Save all units
    await vector_store.save_multiple(modified_units)

    # Find only attraction units
    attraction_units = await vector_store.find_by_target(
        target_id="attraction-001", target_type="attraction"
    )

    # Should only return non-modified units
    assert len(attraction_units) == len(text_units) - 3

    # Find hotel units
    hotel_units = await vector_store.find_by_target(
        target_id="hotel-001", target_type="hotel"
    )

    # Should only return modified units
    assert len(hotel_units) == 3

    # Verify correct filtering
    for unit in attraction_units:
        assert unit.attributes is not None
        assert unit.attributes["target_id"] == "attraction-001"
        assert unit.attributes["target_type"] == "attraction"

    for unit in hotel_units:
        assert unit.attributes is not None
        assert unit.attributes["target_id"] == "hotel-001"
        assert unit.attributes["target_type"] == "hotel"


@pytest.mark.asyncio
async def test_find_by_target_limit(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test that the limit parameter works correctly."""
    # Save text units
    await vector_store.save_multiple(text_units)

    # Find with limit
    limit = 5
    found_units = await vector_store.find_by_target(
        target_id="attraction-001", target_type="attraction", limit=limit
    )

    # Should respect the limit
    assert len(found_units) <= limit


@pytest.mark.asyncio
async def test_find_by_target_no_embedding(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test that retrieved text units don't include embeddings."""
    # Save text units (with embeddings)
    await vector_store.save_multiple(text_units)

    # Retrieve text units
    found_units = await vector_store.find_by_target(
        target_id="attraction-001", target_type="attraction"
    )

    # Verify embeddings are not included in retrieved units
    for unit in found_units:
        # The embedding field should be None since we don't retrieve it
        assert unit.embedding is None


@pytest.mark.asyncio
async def test_save_multiple_upsert_behavior(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test that save_multiple performs upsert (update or insert)."""
    # Save text units first time
    await vector_store.save_multiple(text_units)

    # Modify the text units
    modified_units = text_units.copy()
    for unit in modified_units:
        unit.text = f"MODIFIED: {unit.text[:50]}"

    # Save again with same IDs
    await vector_store.save_multiple(modified_units)

    # Retrieve and verify update
    target_id = "attraction-001"
    target_type = "attraction"
    found_units = await vector_store.find_by_target(
        target_id=target_id, target_type=target_type
    )

    # Should still have same number of units (upsert, not duplicate)
    assert len(found_units) == len(text_units)

    # Verify all texts start with "MODIFIED:"
    for unit in found_units:
        assert unit.text.startswith("MODIFIED:")


@pytest.mark.asyncio
async def test_search_by_vector_success(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test searching text units by embedding vector."""
    # Save text units first
    await vector_store.save_multiple(text_units)

    # Use the first text unit's embedding for search
    query_embedding = text_units[0].embedding
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

    # The first result should be the same text unit (highest similarity)
    assert results[0].text == text_units[0].text

    # All results should have the correct target
    for unit in results:
        assert unit.attributes is not None
        assert unit.attributes["target_id"] == target_id
        assert unit.attributes["target_type"] == target_type


@pytest.mark.asyncio
async def test_search_by_vector_respects_top_k(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test that search_by_vector respects the top_k parameter."""
    # Save text units
    await vector_store.save_multiple(text_units)

    query_embedding = text_units[0].embedding
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
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test that search_by_vector correctly filters by target_id and target_type."""
    # Modify some text units to have different targets
    modified_units = text_units.copy()
    for unit in modified_units[:3]:
        if unit.attributes:
            unit.attributes["target_id"] = "hotel-001"
            unit.attributes["target_type"] = "hotel"

    # Save all units
    await vector_store.save_multiple(modified_units)

    query_embedding = text_units[0].embedding
    assert query_embedding is not None

    # Search for attraction units only
    attraction_results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=10,
    )

    # Should only return attraction units
    assert len(attraction_results) == len(text_units) - 3
    for unit in attraction_results:
        assert unit.attributes is not None
        assert unit.attributes["target_id"] == "attraction-001"
        assert unit.attributes["target_type"] == "attraction"

    # Search for hotel units only
    hotel_results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="hotel-001",
        target_type="hotel",
        top_k=10,
    )

    # Should only return hotel units
    assert len(hotel_results) == 3
    for unit in hotel_results:
        assert unit.attributes is not None
        assert unit.attributes["target_id"] == "hotel-001"
        assert unit.attributes["target_type"] == "hotel"


@pytest.mark.asyncio
async def test_search_by_vector_empty_results(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test search_by_vector with no matching results."""
    # Save text units
    await vector_store.save_multiple(text_units)

    query_embedding = text_units[0].embedding
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
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test that search results are ordered by similarity (score)."""
    # Save text units
    await vector_store.save_multiple(text_units)

    query_embedding = text_units[0].embedding
    assert query_embedding is not None

    # Search by vector
    results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=10,
    )

    # Results should be ordered by similarity
    # The first result should be the queried text unit itself (highest similarity)
    assert len(results) > 1
    assert results[0].text == text_units[0].text


@pytest.mark.asyncio
async def test_search_by_vector_no_embedding_in_results(
    vector_store: TextUnitVectorStore, text_units: list[TextUnit]
) -> None:
    """Test that search results don't include embeddings."""
    # Save text units with embeddings
    await vector_store.save_multiple(text_units)

    query_embedding = text_units[0].embedding
    assert query_embedding is not None

    # Search by vector
    results = await vector_store.search_by_vector(
        embedding_vector=query_embedding,
        target_id="attraction-001",
        target_type="attraction",
        top_k=5,
    )

    # Results should not include embeddings
    for unit in results:
        assert unit.embedding is None
