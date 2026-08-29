from __future__ import annotations

import asyncio
import logging
from typing import Any

import pandas as pd
import pyarrow as pa
from asgiref.sync import async_to_sync
from celery import Task, shared_task
from neo4j import Driver, GraphDatabase
from qdrant_client import AsyncQdrantClient
from tiktoken import encoding_name_for_model

from review_summary.clients.reviews import ReviewServiceClient, TargetType
from review_summary.config.settings import get_settings
from review_summary.index.operations.create_graph import delete_graph_by_target
from review_summary.index.operations.embed_text import embed_text
from review_summary.index.review_snapshot import (
    compute_review_snapshot,
    reviews_to_text_units,
)
from review_summary.infra.nacos.naming import NacosNaming
from review_summary.models import TextUnit
from review_summary.tokenizer.tiktoken import TiktokenTokenizer
from review_summary.utils.storage import get_storage_options
from review_summary.utils.uuid import uuid7
from review_summary.vector_stores.entity import EntityVectorStore
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)
_EMBEDDING_MODEL = "text-embedding-3-large"


class EmptyReviewsError(RuntimeError):
    pass


@shared_task(bind=True)
def run_workflow(self: Task[Any, Any], context: dict[str, Any]) -> dict[str, Any]:
    async_to_sync(_collect_text_units)(self, context)
    return context


async def _collect_text_units(task: Task[Any, Any], context: dict[str, Any]) -> None:
    """Collected `text_units` pyarrow schema:
    | Column           | Type         | Description                                      |
    | :--------------- | :----------- | :----------------------------------------------- |
    | id               | string       | ID of the TextUnit                               |
    | readable_id      | string       | Human-friendly ID of the TextUnit                |
    | text             | string       | Text content of the TextUnit                     |
    | embedding        | list<double> | Embedding vector of the text content             |
    | entity_ids       | list<string> | IDs of Entities extracted from the TextUnit      |
    | relationship_ids | list<string> | IDs of Relationships extracted from the TextUnit |
    | n_tokens         | int64        | Number of tokens of the text content             |
    | document_id      | string       | ID of the source Document of the TextUnit        |
    | attributes       | struct       | Attributes including target information          |
    """  # noqa: E501
    settings = get_settings()
    qdrant_client = AsyncQdrantClient(url=settings.qdrant.url)
    naming: NacosNaming | None = None
    neo4j_driver: Driver | None = None
    try:
        naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        review_client = ReviewServiceClient(naming)
        text_unit_vector_store = await TextUnitVectorStore.create_vector_store(
            client=qdrant_client, vector_dim=context.get("vector_dim", 3072)
        )
        entity_vector_store = await EntityVectorStore.create_vector_store(
            client=qdrant_client, vector_dim=context.get("vector_dim", 3072)
        )
        neo4j_driver = GraphDatabase.driver(  # pyright: ignore
            uri=settings.neo4j.uri,
            auth=(
                settings.neo4j.username,
                settings.neo4j.password.get_secret_value(),
            ),
        )
        await _internal(
            task,
            context,
            review_client,
            text_unit_vector_store,
            entity_vector_store,
            neo4j_driver,
        )

    finally:
        try:
            if naming is not None:
                await naming.shutdown()
        finally:
            try:
                if neo4j_driver is not None:
                    neo4j_driver.close()
            finally:
                await qdrant_client.close()


async def _internal(
    task: Task[Any, Any],
    context: dict[str, Any],
    review_client: ReviewServiceClient,
    text_unit_vector_store: TextUnitVectorStore,
    entity_vector_store: EntityVectorStore,
    neo4j_driver: Driver,
) -> None:
    target_id = context["target_id"]
    target_type = TargetType(context["target_type"])

    reviews = await review_client.list_all(target_id, target_type)
    review_snapshot = compute_review_snapshot(reviews)
    context["review_snapshot"] = review_snapshot
    context["review_count"] = len(reviews)

    if not reviews:
        await _clear_target_index(
            target_id,
            target_type,
            text_unit_vector_store,
            entity_vector_store,
            neo4j_driver,
        )
        raise EmptyReviewsError(
            f"No reviews found for {target_type.value} {target_id}; stale index cleared"
        )

    text_units = reviews_to_text_units(
        reviews,
        target_id,
        target_type,
        review_snapshot,
    )
    await _prepare_embeddings(text_units)
    filename = _save_text_units(text_units)

    await _clear_target_index(
        target_id,
        target_type,
        text_unit_vector_store,
        entity_vector_store,
        neo4j_driver,
    )
    await text_unit_vector_store.save_multiple(text_units)

    message = (
        f"Collected and indexed {len(text_units)} reviews for "
        f"{target_type.value} {target_id} at snapshot {review_snapshot}."
    )
    logger.info(message)
    task.update_state(
        state="PROGRESS",
        meta={
            "description": message,
            "target_id": target_id,
            "target_type": target_type.value,
            "collected_text_units": len(text_units),
            "review_snapshot": review_snapshot,
        },
    )
    context["text_units"] = filename


async def _prepare_embeddings(text_units: list[TextUnit]) -> None:
    embeddings = await embed_text(
        [text_unit.text for text_unit in text_units],
        {"model": _EMBEDDING_MODEL},
    )
    if len(embeddings) != len(text_units) or any(
        embedding is None for embedding in embeddings
    ):
        raise RuntimeError("Failed to create an embedding for every review")

    tokenizer = TiktokenTokenizer(encoding_name_for_model(_EMBEDDING_MODEL))
    for text_unit, embedding in zip(text_units, embeddings, strict=True):
        if embedding is None:
            raise RuntimeError("Review embedding unexpectedly missing")
        text_unit.embedding = embedding
        text_unit.n_tokens = tokenizer.num_tokens(text_unit.text)


async def _clear_target_index(
    target_id: str,
    target_type: TargetType,
    text_unit_vector_store: TextUnitVectorStore,
    entity_vector_store: EntityVectorStore,
    neo4j_driver: Driver,
) -> None:
    await text_unit_vector_store.delete_by_target(target_id, target_type.value)
    await entity_vector_store.delete_by_target(target_id, target_type.value)
    await asyncio.to_thread(
        delete_graph_by_target,
        neo4j_driver,
        target_id,
        target_type.value,
    )


def _save_text_units(text_units: list[TextUnit]) -> str:
    df = pd.DataFrame([text_unit.model_dump() for text_unit in text_units])
    list_string_columns = ["entity_ids", "relationship_ids"]
    df[list_string_columns] = df[list_string_columns].astype(
        pd.ArrowDtype(pa.list_(pa.string()))
    )

    filename = f"text_units_{uuid7()}.parquet"
    df.to_parquet(
        f"s3://review-summary/{filename}",
        storage_options=get_storage_options(),
    )
    logger.info(f"Saved text units to 's3://review-summary/{filename}'.")
    return filename
