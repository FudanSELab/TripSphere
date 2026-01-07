from __future__ import annotations

from typing import Any

import pandas as pd
from asgiref.sync import async_to_sync
from celery import Task, shared_task
from qdrant_client import AsyncQdrantClient

from review_summary.config.index.create_text_embeddings_config import (
    CreateTextEmbeddingsConfig,
)
from review_summary.config.settings import get_settings
from review_summary.index.operations.embed_text import embed_text
from review_summary.models import Entity
from review_summary.utils.storage import get_storage_options
from review_summary.vector_stores.entity import EntityVectorStore


@shared_task(bind=True)
def run_workflow(
    self: Task[Any, Any], context: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    async_to_sync(_create_text_embeddings)(
        self, context, CreateTextEmbeddingsConfig.model_validate(config)
    )
    return context


async def _create_text_embeddings(
    task: Task[Any, Any], context: dict[str, Any], config: CreateTextEmbeddingsConfig
) -> None:
    qdrant_settings = get_settings().qdrant
    qdrant_client = AsyncQdrantClient(url=qdrant_settings.url)
    try:
        entity_vector_store = await EntityVectorStore.create_vector_store(
            client=qdrant_client, vector_dim=context.get("vector_dim", 3072)
        )
        await _internal(task, context, config, entity_vector_store)

    finally:
        await qdrant_client.close()  # Ensure the client is closed properly


async def _internal(
    task: Task[Any, Any],
    context: dict[str, Any],
    config: CreateTextEmbeddingsConfig,
    entity_vector_store: EntityVectorStore,
) -> None:
    entities: pd.DataFrame | None = None
    if "entities" in config.fields_to_embed:
        entities_filename = context["entities"]
        entities = pd.read_parquet(
            f"s3://review-summary/{entities_filename}",
            storage_options=get_storage_options(),
            dtype_backend="pyarrow",
        )

    if entities is not None:
        for column_name in config.fields_to_embed.get("entities", []):
            entities[f"{column_name}_embedding"] = await embed_text(  # type: ignore
                texts=entities[column_name].tolist(),
                batch_size=config.batch_size,
                batch_max_tokens=config.batch_max_tokens,
                embedding_model_config=config.embedding_llm_config,
            )

    # Save entities with embeddings to vector store
    if entities is not None:
        await entity_vector_store.save_multiple(
            [Entity.model_validate(row.to_dict()) for _, row in entities.iterrows()]
        )
