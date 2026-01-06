from typing import Any

import pandas as pd
import pytest
from pytest_mock import MockerFixture, MockType
from qdrant_client import AsyncQdrantClient

from review_summary.index.tasks.create_final_text_units import (
    _internal,  # pyright: ignore
)
from review_summary.models import TextUnit
from review_summary.vector_stores.text_unit import TextUnitVectorStore


@pytest.mark.asyncio
async def test_create_final_text_units(
    mock_task: MockType,
    text_units_parquet_uuid: str,
    final_graph_parquet_uuid: str,
    text_units: list[TextUnit],
    mocker: MockerFixture,
) -> None:
    # Mock pandas.read_parquet to read from local fixtures instead of S3
    original_read_parquet = pd.read_parquet

    def _mock_read_parquet(path: str, **kwargs: Any) -> pd.DataFrame:
        # Redirect S3 paths to local fixtures
        if path.startswith("s3://review-summary/"):
            filename = path.replace("s3://review-summary/", "")
            local_path = f"tests/fixtures/{filename}"
            # Remove storage_options to avoid S3 connection
            kwargs.pop("storage_options", None)
            return original_read_parquet(local_path, **kwargs)
        return original_read_parquet(path, **kwargs)

    mocker.patch("pandas.read_parquet", side_effect=_mock_read_parquet)

    # Pre-save text units to the vector store
    qdrant_client = AsyncQdrantClient(":memory:")
    vector_store = await TextUnitVectorStore.create_vector_store(
        client=qdrant_client, vector_dim=3072
    )
    await vector_store.save_multiple(text_units)

    mock_task_update_state: MockType = mock_task.update_state
    mock_task_update_state.return_value = None

    try:
        context = {
            "target_id": "attraction-001",
            "target_type": "attraction",
            "text_units": f"text_units_{text_units_parquet_uuid}.parquet",
            "entities": f"entities_{final_graph_parquet_uuid}.parquet",
            "relationships": f"relationships_{final_graph_parquet_uuid}.parquet",
        }
        await _internal(mock_task, context, vector_store)

        # Add assertions as needed to verify the behavior
        df = (
            pd.read_parquet(
                f"tests/fixtures/text_units_{text_units_parquet_uuid}.parquet",
                dtype_backend="pyarrow",
            )
            .sort_values(by="id", ascending=True)
            .reset_index(drop=True)
        )
        mock_task_update_state.assert_has_calls(
            [
                mocker.call(  # pyright: ignore[reportArgumentType]
                    state="PROGRESS",
                    meta={"description": f"Aggregated {len(df)} final text units."},
                )
            ]
        )

        # Make sure the TextUnits are saved in the vector store
        stored_text_units = await vector_store.find_by_target(
            target_id="attraction-001", target_type="attraction", limit=1024
        )
        sorted_text_units = sorted(stored_text_units, key=lambda tu: tu.id)
        assert len(stored_text_units) == len(df)
        for i, unit in enumerate(sorted_text_units):
            assert unit.id == df.iloc[i]["id"]
            assert unit.readable_id == df.iloc[i]["readable_id"]
            assert unit.text == df.iloc[i]["text"]
            assert unit.document_id == df.iloc[i]["document_id"]
            assert unit.n_tokens == df.iloc[i]["n_tokens"]
            assert unit.attributes == df.iloc[i]["attributes"]

    finally:
        await qdrant_client.close()
