import json
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture, MockType

from review_summary.models import TextUnit
from review_summary.rocketmq.handlers import handle_create_review


@pytest.fixture
def mock_vector_store(mocker: MockerFixture) -> MockType:
    """Mock TextUnitVectorStore."""
    mock_store = mocker.AsyncMock()
    mock_store.save_multiple = mocker.AsyncMock()
    return mock_store


@pytest.fixture
def reviews_data() -> list[dict[str, Any]]:
    """Load reviews from fixtures file."""
    fixtures_path = Path(__file__).parent.parent.parent / "fixtures" / "reviews.json"
    with open(fixtures_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_handle_create_review(
    mock_vector_store: MockType,
    reviews_data: list[dict[str, Any]],
    mocker: MockerFixture,
) -> None:
    """Test handle_create_review with real LLM embeddings and save results locally."""
    # Create output directory if not exists
    output_dir = Path("tests/fixtures/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_text_units: list[TextUnit] = []

    async def capture_text_units(text_units: list[TextUnit]) -> None:
        all_text_units.extend(text_units)

    mock_vector_store.save_multiple.side_effect = capture_text_units

    for review_data in reviews_data:
        # Convert fixture format to CreateReview message format
        message = {
            "ID": review_data["review_id"],
            "Text": review_data["text"],
            "TargetID": review_data["target_id"],
        }

        # Execute the handler
        await handle_create_review(mock_vector_store, message)

    # Verify text units structure
    for text_unit in all_text_units:
        # Find which review this text unit belongs to
        review_data = next(
            (r for r in reviews_data if r["review_id"] == text_unit.document_id),
            None,
        )

        assert review_data is not None
        assert text_unit.document_id == review_data["review_id"]

        assert text_unit.attributes is not None
        assert text_unit.attributes["target_id"] == review_data["target_id"]
        assert text_unit.attributes["target_type"] == "attraction"

        assert text_unit.embedding is not None
        assert len(text_unit.embedding) == 3072

        assert text_unit.n_tokens is not None
        assert text_unit.n_tokens > 0

        assert text_unit.short_id is not None
        assert text_unit.short_id.startswith(
            f"/reviews/{review_data['review_id']}/text-units/"
        )

    # Save all text units to a single JSON file
    if all_text_units:
        output_file = output_dir / "text_units.json"
        text_units_data = [unit.model_dump() for unit in all_text_units]
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(text_units_data, f, indent=2, ensure_ascii=False)

    # Verify all reviews were processed
    assert len(reviews_data) == 5
    assert len(all_text_units) > 0
