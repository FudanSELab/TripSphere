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
