from typing import Any

import polars as pl
import pytest
from pytest_mock import MockerFixture, MockType

import review_summary.infra.celery.monkey_patch as celery_monkey_patch
from review_summary.config.index.extract_graph_config import ExtractGraphConfig
from review_summary.index.tasks.extract_graph import _extract_graph  # pyright: ignore

_ = celery_monkey_patch  # Make pyright happy


@pytest.mark.asyncio
async def test_extract_graph(
    mock_task: MockType,
    text_units_parquet_uuid: str,
    entities_parquet_uuid: str,
    relationships_parquet_uuid: str,
    mocker: MockerFixture,
) -> None:
    # Mock uuid7 to return fixed UUIDs
    mocker.patch(
        "review_summary.index.tasks.extract_graph.uuid7",
        side_effect=[entities_parquet_uuid, relationships_parquet_uuid],
    )

    # Mock pl.scan_parquet to read from local fixtures instead of S3
    original_scan_parquet = pl.scan_parquet

    def mock_scan_parquet(path: str, **kwargs: Any) -> pl.LazyFrame:
        # Redirect S3 paths to local fixtures
        if path.startswith("s3://review-summary/"):
            filename = path.replace("s3://review-summary/", "")
            local_path = f"tests/fixtures/{filename}"
            # Remove storage_options to avoid S3 connection
            kwargs.pop("storage_options", None)
            return original_scan_parquet(local_path, **kwargs)
        return original_scan_parquet(path, **kwargs)

    mocker.patch("polars.scan_parquet", side_effect=mock_scan_parquet)

    # Mock write_parquet to save locally
    original_write_parquet = pl.DataFrame.write_parquet

    def mock_write_parquet(self: pl.DataFrame, path: str, **kwargs: Any) -> None:
        if path.startswith("s3://review-summary/"):
            filename = path.replace("s3://review-summary/", "")
            local_path = f"tests/fixtures/output/{filename}"
            # Remove storage_options to avoid S3 connection
            kwargs.pop("storage_options", None)
            original_write_parquet(self, local_path, **kwargs)
        else:
            original_write_parquet(self, path, **kwargs)

    mocker.patch(
        "polars.DataFrame.write_parquet", side_effect=mock_write_parquet, autospec=True
    )

    context = {
        "target_id": "attraction-001",
        "target_type": "attraction",
        "text_units": f"text_units_{text_units_parquet_uuid}.parquet",
    }
    config = ExtractGraphConfig(
        graph_llm_config={"name": "gpt-4o", "temperature": 0.0},
        summary_llm_config={"name": "gpt-4o", "temperature": 0.0},
    )

    await _extract_graph(mock_task, context, config)

    # Add assertions as needed to verify the behavior
    assert context["entities"] == f"entities_{entities_parquet_uuid}.parquet"
    assert (
        context["relationships"]
        == f"relationships_{relationships_parquet_uuid}.parquet"
    )
