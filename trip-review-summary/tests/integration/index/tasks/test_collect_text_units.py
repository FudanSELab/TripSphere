from typing import Any

import pandas as pd
import pytest
from pytest_mock import MockerFixture, MockType

from review_summary.index.tasks.collect_text_units import _internal  # pyright: ignore
from review_summary.models import TextUnit


@pytest.mark.asyncio
async def test_collect_text_units(
    mock_task: MockType,
    text_units_parquet_uuid: str,
    text_units: list[TextUnit],
    mocker: MockerFixture,
) -> None:
    # Mock uuid7 to return fixed UUIDs
    mocker.patch(
        "review_summary.index.tasks.collect_text_units.uuid7",
        return_value=text_units_parquet_uuid,
    )

    # Mock write_parquet to save locally
    original_to_parquet = pd.DataFrame.to_parquet

    def _mock_to_parquet(self: pd.DataFrame, file: str, **kwargs: Any) -> None:
        if file.startswith("s3://review-summary/"):
            filename = file.replace("s3://review-summary/", "")
            local_path = f"tests/fixtures/output/{filename}"
            # Remove storage_options to avoid S3 connection
            kwargs.pop("storage_options", None)
            return original_to_parquet(self, local_path, **kwargs)
        return original_to_parquet(self, file, **kwargs)

    mocker.patch.object(pd.DataFrame, "to_parquet", _mock_to_parquet)

    # Mock TextUnitVectorStore find_by_target
    mock_vector_store: MockType = mocker.AsyncMock()
    find_by_target: MockType = mock_vector_store.find_by_target
    find_by_target.return_value = text_units

    update_state: MockType = mock_task.update_state
    update_state.return_value = None

    context = {"target_id": "attraction-001", "target_type": "attraction"}
    await _internal(mock_task, context, mock_vector_store)

    find_by_target.assert_awaited_once_with("attraction-001", "attraction")
    collected_text_units = len(text_units)
    update_state.assert_called_once_with(
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
