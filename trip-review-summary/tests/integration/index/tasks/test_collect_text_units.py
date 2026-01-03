from typing import Any

import polars as pl
import pytest
from pytest_mock import MockerFixture, MockType

import review_summary.infra.celery.monkey_patch as celery_monkey_patch
from review_summary.index.tasks.collect_text_units import (
    _collect_text_units,  # pyright: ignore
)
from review_summary.models import TextUnit

_ = celery_monkey_patch  # Make pyright happy


@pytest.fixture(autouse=True)
def mock_qdrant_client(mocker: MockerFixture) -> MockType:
    mock_qdrant_client: MockType = mocker.AsyncMock()
    mocker.patch(
        "review_summary.index.tasks.collect_text_units.AsyncQdrantClient",
        return_value=mock_qdrant_client,
    )
    return mock_qdrant_client


@pytest.fixture
def mock_vector_store(mocker: MockerFixture) -> MockType:
    mock_vector_store: MockType = mocker.AsyncMock()
    mocker.patch(
        (
            "review_summary.index.tasks.collect_text_units"
            ".TextUnitVectorStore.create_vector_store"
        ),
        return_value=mock_vector_store,
    )
    return mock_vector_store


@pytest.mark.asyncio
async def test_collect_text_units(
    mock_task: MockType,
    text_units_parquet_uuid: str,
    text_units: list[TextUnit],
    mock_vector_store: MockType,
    mocker: MockerFixture,
) -> None:
    # Store original write_parquet method
    original_write_parquet = pl.DataFrame.write_parquet

    def save_parquet_locally(self: pl.DataFrame, path: str, **kwargs: Any) -> None:
        filename = f"text_units_{text_units_parquet_uuid}.parquet"
        # Call the original method with local path
        original_write_parquet(self, f"tests/fixtures/output/{filename}")

    mocker.patch(
        "review_summary.index.tasks.collect_text_units.uuid7",
        return_value=text_units_parquet_uuid,
    )
    mocker.patch(
        "polars.DataFrame.write_parquet",
        side_effect=save_parquet_locally,
        autospec=True,
    )
    update_statue: MockType = mock_task.update_state
    update_statue.return_value = None
    find_by_target: MockType = mock_vector_store.find_by_target
    find_by_target.return_value = text_units

    context = {
        "target_id": "attraction-001",
        "target_type": "attraction",
    }
    await _collect_text_units(mock_task, context)

    find_by_target.assert_awaited_once_with("attraction-001", "attraction")
    collected_text_units = len(text_units)
    update_statue.assert_called_once_with(
        state="PROGRESS",
        meta={
            "description": (
                f"Collected {collected_text_units} text units "
                "for attraction attraction-001."
            ),
            "target_id": "attraction-001",
            "target_type": "attraction",
            "collected_text_units": collected_text_units,
        },
    )
    assert context["text_units"] == f"text_units_{text_units_parquet_uuid}.parquet"
