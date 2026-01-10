from typing import Any

import numpy as np
import pandas as pd
import pytest
import pytest_asyncio
from pytest_mock import MockerFixture, MockType
from qdrant_client import AsyncQdrantClient

from review_summary.config.index.create_text_embeddings_config import (
    CreateTextEmbeddingsConfig,
)
from review_summary.index.tasks.create_text_embeddings import (
    _internal,  # pyright: ignore
)
from review_summary.vector_stores.entity import EntityVectorStore


@pytest_asyncio.fixture
async def qdrant_client() -> AsyncQdrantClient:
    """Create an in-memory Qdrant client for testing."""
    client = AsyncQdrantClient(":memory:")
    return client


@pytest_asyncio.fixture
async def entity_vector_store(qdrant_client: AsyncQdrantClient) -> EntityVectorStore:
    """Create an EntityVectorStore with in-memory client."""
    return await EntityVectorStore.create_vector_store(
        client=qdrant_client, vector_dim=3072
    )


@pytest.mark.asyncio
async def test_create_text_embeddings(
    mock_task: MockType,
    final_graph_parquet_uuid: str,
    qdrant_client: AsyncQdrantClient,
    entity_vector_store: EntityVectorStore,
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

    # Mock embed_text to return fake embeddings
    async def _mock_embed_text(
        texts: list[str],
        batch_size: int,
        batch_max_tokens: int,
        embedding_model_config: dict[str, Any],
    ) -> list[list[float]]:
        # Return a list of fake embeddings (3072 dimensions) for each text
        return [np.random.rand(3072).tolist() for _ in texts]

    mocker.patch(
        "review_summary.index.tasks.create_text_embeddings.embed_text",
        side_effect=_mock_embed_text,
    )

    try:
        context = {
            "target_id": "attraction-001",
            "target_type": "attraction",
            "entities": f"entities_{final_graph_parquet_uuid}.parquet",
            "vector_dim": 3072,
        }
        config = CreateTextEmbeddingsConfig(
            embedding_llm_config={"name": "text-embedding-3-large"},
            batch_size=16,
            batch_max_tokens=8191,
            fields_to_embed={"entities": ["description"]},
        )

        await _internal(mock_task, context, config, entity_vector_store)

        # Verify that entities were saved to the vector store
        collection_info = await qdrant_client.get_collection(
            collection_name=EntityVectorStore.COLLECTION_NAME
        )
        assert collection_info.points_count and collection_info.points_count > 0

        # Read the entities from the parquet to verify the count
        entities_df = pd.read_parquet(
            f"tests/fixtures/entities_{final_graph_parquet_uuid}.parquet",
            dtype_backend="pyarrow",
        )
        # Should have saved all entities with description embeddings
        assert collection_info.points_count == len(entities_df)

    finally:
        await qdrant_client.close()


@pytest.mark.asyncio
async def test_create_text_embeddings_with_multiple_fields(
    mock_task: MockType,
    final_graph_parquet_uuid: str,
    qdrant_client: AsyncQdrantClient,
    entity_vector_store: EntityVectorStore,
    mocker: MockerFixture,
) -> None:
    """Test creating embeddings for multiple fields (title and description)."""
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

    # Mock embed_text to return fake embeddings
    async def _mock_embed_text(
        texts: list[str],
        batch_size: int,
        batch_max_tokens: int,
        embedding_model_config: dict[str, Any],
    ) -> list[list[float]]:
        # Return a list of fake embeddings (3072 dimensions) for each text
        return [np.random.rand(3072).tolist() for _ in texts]

    mocker.patch(
        "review_summary.index.tasks.create_text_embeddings.embed_text",
        side_effect=_mock_embed_text,
    )

    try:
        context = {
            "target_id": "attraction-001",
            "target_type": "attraction",
            "entities": f"entities_{final_graph_parquet_uuid}.parquet",
            "vector_dim": 3072,
        }
        config = CreateTextEmbeddingsConfig(
            embedding_llm_config={"name": "text-embedding-3-large"},
            batch_size=16,
            batch_max_tokens=8191,
            fields_to_embed={"entities": ["description", "title"]},
        )

        await _internal(mock_task, context, config, entity_vector_store)

        # Verify that entities were saved to the vector store
        collection_info = await qdrant_client.get_collection(
            collection_name=EntityVectorStore.COLLECTION_NAME
        )
        assert collection_info.points_count and collection_info.points_count > 0

        # Read the entities from the parquet to verify the count
        entities_df = pd.read_parquet(
            f"tests/fixtures/entities_{final_graph_parquet_uuid}.parquet",
            dtype_backend="pyarrow",
        )
        # Should have saved all entities with both description and title embeddings
        assert collection_info.points_count == len(entities_df)

    finally:
        await qdrant_client.close()


@pytest.mark.asyncio
async def test_create_text_embeddings_empty_entities(
    mock_task: MockType,
    qdrant_client: AsyncQdrantClient,
    entity_vector_store: EntityVectorStore,
    mocker: MockerFixture,
) -> None:
    """Test creating embeddings when entities field is not in fields_to_embed."""

    try:
        context = {
            "target_id": "attraction-001",
            "target_type": "attraction",
            "vector_dim": 3072,
        }
        config = CreateTextEmbeddingsConfig(
            embedding_llm_config={"name": "text-embedding-3-large"},
            batch_size=16,
            batch_max_tokens=8191,
            fields_to_embed={},  # No fields to embed
        )

        await _internal(mock_task, context, config, entity_vector_store)

        # Verify that no entities were saved
        collection_info = await qdrant_client.get_collection(
            collection_name=EntityVectorStore.COLLECTION_NAME
        )
        assert collection_info.points_count == 0

    finally:
        await qdrant_client.close()
