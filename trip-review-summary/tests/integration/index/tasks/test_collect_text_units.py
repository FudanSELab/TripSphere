from typing import Any

import pandas as pd
import pytest
from pytest_mock import MockerFixture, MockType
from qdrant_client import AsyncQdrantClient

from review_summary.index.tasks.collect_text_units import _internal  # pyright: ignore
from review_summary.models import TextUnit
from review_summary.vector_stores.text_unit import TextUnitVectorStore


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

    # Pre-save text units to the vector store
    qdrant_client = AsyncQdrantClient(":memory:")
    vector_store = await TextUnitVectorStore.create_vector_store(
        client=qdrant_client, vector_dim=3072
    )
    await vector_store.save_multiple(text_units)

    mock_task_update_state: MockType = mock_task.update_state
    mock_task_update_state.return_value = None

    try:
        context = {"target_id": "attraction-001", "target_type": "attraction"}
        await _internal(mock_task, context, vector_store)

    finally:
        await qdrant_client.close()

    collected_text_units = len(text_units)
    mock_task_update_state.assert_has_calls(
        [
            mocker.call(  # pyright: ignore[reportArgumentType]
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
            ),
        ]
    )
    assert context["text_units"] == f"text_units_{text_units_parquet_uuid}.parquet"

    # Make sure the parquet content is correct
    df = pd.read_parquet(
        f"tests/fixtures/output/text_units_{text_units_parquet_uuid}.parquet",
        dtype_backend="pyarrow",
    )
    assert len(df) == len(text_units)
    for i, unit in enumerate(text_units):
        assert df.iloc[i]["id"] == unit.id
        assert df.iloc[i]["text"] == unit.text
