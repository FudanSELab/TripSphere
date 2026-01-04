import logging
from typing import Any

import polars as pl
import pytest
from neo4j import AsyncGraphDatabase
from pytest_mock import MockerFixture, MockType

from review_summary.config.index.finalize_graph_config import FinalizeGraphConfig
from review_summary.config.settings import get_settings
from review_summary.index.tasks.finalize_graph import _internal  # pyright: ignore

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_finalize_graph(
    mock_task: MockType,
    graph_parquet_uuid: str,
    final_graph_parquet_uuid: str,
    mocker: MockerFixture,
) -> None:
    # Mock pl.scan_parquet to read from local fixtures instead of S3
    original_scan_parquet = pl.scan_parquet

    def _mock_scan_parquet(path: str, **kwargs: Any) -> pl.LazyFrame:
        # Redirect S3 paths to local fixtures
        if path.startswith("s3://review-summary/"):
            filename = path.replace("s3://review-summary/", "")
            local_path = f"tests/fixtures/{filename}"
            # Remove storage_options to avoid S3 connection
            kwargs.pop("storage_options", None)
            return original_scan_parquet(local_path, **kwargs)
        return original_scan_parquet(path, **kwargs)

    mocker.patch("polars.scan_parquet", side_effect=_mock_scan_parquet)

    # Mock write_parquet to save locally
    original_write_parquet = pl.DataFrame.write_parquet

    def _mock_write_parquet(self: pl.DataFrame, file: str, **kwargs: Any) -> None:
        if file.startswith("s3://review-summary/"):
            filename = file.replace("s3://review-summary/", "")
            local_path = f"tests/fixtures/output/{filename}"
            # Remove storage_options to avoid S3 connection
            kwargs.pop("storage_options", None)
            return original_write_parquet(self, local_path, **kwargs)
        return original_write_parquet(self, file, **kwargs)

    mocker.patch.object(pl.DataFrame, "write_parquet", _mock_write_parquet)

    context = {
        "target_id": "attraction-001",
        "target_type": "attraction",
        "entities": f"entities_{graph_parquet_uuid}.parquet",
        "relationships": f"relationships_{graph_parquet_uuid}.parquet",
    }
    config = FinalizeGraphConfig()
    settings = get_settings()
    neo4j_driver = AsyncGraphDatabase.driver(  # pyright: ignore
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password.get_secret_value()),
    )
    try:
        await _internal(
            mock_task,
            context,
            config,
            neo4j_driver,
            checkpoint_id=final_graph_parquet_uuid,
        )

    finally:
        await neo4j_driver.close()  # Ensure the driver is closed properly

    # Add assertions as needed to verify the behavior
    assert context["entities"] == f"entities_{final_graph_parquet_uuid}.parquet"
    assert (
        context["relationships"] == f"relationships_{final_graph_parquet_uuid}.parquet"
    )
