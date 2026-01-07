from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import pyarrow as pa
from asgiref.sync import async_to_sync
from celery import Task, shared_task
from qdrant_client import AsyncQdrantClient

from review_summary.config.settings import get_settings
from review_summary.utils.storage import get_storage_options
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_workflow(self: Task[Any, Any], context: dict[str, Any]) -> dict[str, Any]:
    async_to_sync(_create_final_text_units)(self, context)
    return context


async def _create_final_text_units(
    task: Task[Any, Any], context: dict[str, Any]
) -> None:
    """Final `text_units` pyarrow schema:
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
    qdrant_settings = get_settings().qdrant
    qdrant_client = AsyncQdrantClient(url=qdrant_settings.url)
    try:
        text_unit_vector_store = await TextUnitVectorStore.create_vector_store(
            client=qdrant_client, vector_dim=context.get("vector_dim", 3072)
        )
        await _internal(task, context, text_unit_vector_store)

    finally:
        await qdrant_client.close()  # Ensure the client is closed properly


async def _internal(
    task: Task[Any, Any],
    context: dict[str, Any],
    text_unit_vector_store: TextUnitVectorStore,
) -> None:
    text_units_filename = context["text_units"]
    entities_filename = context["entities"]
    relationships_filename = context["relationships"]
    text_units = pd.read_parquet(
        f"s3://review-summary/{text_units_filename}",
        storage_options=get_storage_options(),
        dtype_backend="pyarrow",
    )
    final_entities = pd.read_parquet(
        f"s3://review-summary/{entities_filename}",
        storage_options=get_storage_options(),
        dtype_backend="pyarrow",
    )
    final_relationships = pd.read_parquet(
        f"s3://review-summary/{relationships_filename}",
        storage_options=get_storage_options(),
        dtype_backend="pyarrow",
    )

    logger.info("Joining final entities and relationships to text units.")
    entity_join = _entities(final_entities)
    relationship_join = _relationships(final_relationships)

    selected = text_units.loc[
        :,
        [
            "id",
            "readable_id",
            "text",
            "embedding",
            "document_id",
            "n_tokens",
            "attributes",
        ],
    ]
    entity_joined = _join(selected, entity_join)
    relationship_joined = _join(entity_joined, relationship_join)
    final_joined = relationship_joined

    aggregated = final_joined.groupby("id", sort=False).agg("first").reset_index()  # pyright: ignore
    list_string_columns = ["entity_ids", "relationship_ids"]
    aggregated[list_string_columns] = aggregated[list_string_columns].astype(
        pd.ArrowDtype(pa.list_(pa.string()))
    )

    message = f"Aggregated {len(aggregated)} final text units."
    logger.info(message)
    task.update_state(state="PROGRESS", meta={"description": message})

    # Save final text units into Qdrant vector store
    await text_unit_vector_store.update_final_text_units(aggregated)
    logger.info("Final text units saved to vector store.")


def _entities(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_ids"]]
    unrolled = selected.explode(["text_unit_ids"]).reset_index(drop=True)

    return (
        unrolled.groupby("text_unit_ids", sort=False)  # pyright: ignore
        .agg(entity_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_ids": "id"})
    )


def _relationships(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_ids"]]
    unrolled = selected.explode(["text_unit_ids"]).reset_index(drop=True)

    return (
        unrolled.groupby("text_unit_ids", sort=False)  # pyright: ignore
        .agg(relationship_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_ids": "id"})
    )


def _join(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    return left.merge(right, on="id", how="left", suffixes=["_1", "_2"])
