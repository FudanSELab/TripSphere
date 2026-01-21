from typing import Any

import pandas as pd
import pytest
from pytest_mock import MockerFixture, MockType

from review_summary.config.index.extract_graph_config import ExtractGraphConfig
from review_summary.index.tasks.extract_graph import _extract_graph  # pyright: ignore


@pytest.mark.slow
@pytest.mark.asyncio
async def test_extract_graph(
    mock_task: MockType,
    text_units_parquet_uuid: str,
    graph_parquet_uuid: str,
    mocker: MockerFixture,
) -> None:
    # Mock uuid7 to return fixed UUIDs
    mocker.patch(
        "review_summary.index.tasks.extract_graph.uuid7",
        return_value=graph_parquet_uuid,
    )

    # Mock pd.read_parquet to read from local fixtures instead of S3
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

    # Mock write_parquet to save locally
    original_write_parquet = pd.DataFrame.to_parquet

    def _mock_to_parquet(self: pd.DataFrame, file: str, **kwargs: Any) -> None:
        if file.startswith("s3://review-summary/"):
            filename = file.replace("s3://review-summary/", "")
            local_path = f"tests/fixtures/output/{filename}"
            # Remove storage_options to avoid S3 connection
            kwargs.pop("storage_options", None)
            return original_write_parquet(self, local_path, **kwargs)
        return original_write_parquet(self, file, **kwargs)

    mocker.patch.object(pd.DataFrame, "to_parquet", _mock_to_parquet)

    context = {
        "target_id": "attraction-001",
        "target_type": "attraction",
        "text_units": f"text_units_{text_units_parquet_uuid}.parquet",
    }
    config = ExtractGraphConfig(
        graph_llm_config={"model": "gpt-4o", "temperature": 0.0},
        summary_llm_config={"model": "gpt-4o", "temperature": 0.0},
    )
    await _extract_graph(mock_task, context, config)

    # Add assertions as needed to verify the behavior
    assert context["entities"] == f"entities_{graph_parquet_uuid}.parquet"
    assert context["relationships"] == f"relationships_{graph_parquet_uuid}.parquet"
