import asyncio
import logging
from typing import Any

import polars as pl
from langchain_openai import ChatOpenAI

from review_summary.config.settings import get_settings
from review_summary.index.operations.extract_graph.graph_extractor import GraphExtractor
from review_summary.index.operations.extract_graph.typing import ExtractionResult, Unit
from review_summary.utils.networkx import to_polars_edgelist

logger = logging.getLogger(__name__)


async def extract_graph(
    text_units: pl.LazyFrame,
    text_column: str,
    id_column: str,
    entity_types: list[str],
    chat_model_config: dict[str, Any],
    max_gleanings: int = 1,
    tuple_delimiter: str | None = None,
    record_delimiter: str | None = None,
    completion_delimiter: str | None = None,
    extraction_prompt: str | None = None,
    num_concurrency: int = 4,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    semaphore = asyncio.Semaphore(num_concurrency)

    # Initialize ChatOpenAI model with provided config
    openai_settings = get_settings().openai
    if "api_key" not in chat_model_config:
        chat_model_config["api_key"] = openai_settings.api_key
    if "base_url" not in chat_model_config:
        chat_model_config["base_url"] = openai_settings.base_url
    chat_model = ChatOpenAI(**chat_model_config)
    logger.debug("Initialized ChatOpenAI model for graph extraction.")

    async def _process_row(row: dict[str, Any]) -> ExtractionResult:
        async with semaphore:
            return await _run_graph_extraction(
                units=[Unit(id=row[id_column], text=row[text_column])],
                entity_types=entity_types,
                chat_model=chat_model,
                max_gleanings=max_gleanings,
                tuple_delimiter=tuple_delimiter,
                record_delimiter=record_delimiter,
                completion_delimiter=completion_delimiter,
                extraction_prompt=extraction_prompt,
            )

    text_units_df = text_units.select([id_column, text_column]).collect()
    # Gather all results concurrently with semaphore control
    results = await asyncio.gather(
        *[_process_row(row) for row in text_units_df.iter_rows(named=True)]
    )

    entity_lfs: list[pl.LazyFrame] = []
    relationship_lfs: list[pl.LazyFrame] = []
    for result in results:
        entity_lfs.append(result.entities)
        relationship_lfs.append(result.relationships)

    entities = _merge_entities(entity_lfs)
    relationships = _merge_relationships(relationship_lfs)

    return entities, relationships


def _merge_entities(entity_lfs: list[pl.LazyFrame]) -> pl.DataFrame:
    all_entities = pl.concat(entity_lfs, how="vertical")
    return (
        all_entities.group_by(["title", "type"], maintain_order=True)
        .agg(
            pl.col("description"),
            pl.col("source_id").alias("text_unit_ids"),
            pl.col("source_id").count().alias("frequency"),
        )
        .collect()
    )


def _merge_relationships(relationship_lfs: list[pl.LazyFrame]) -> pl.DataFrame:
    all_relationships = pl.concat(relationship_lfs, how="vertical")
    return (
        all_relationships.group_by(["source", "target"], maintain_order=True)
        .agg(
            pl.col("description"),
            pl.col("source_id").alias("text_unit_ids"),
            pl.col("weight").sum().alias("weight"),
        )
        .collect()
    )


async def _run_graph_extraction(
    units: list[Unit],
    entity_types: list[str],
    chat_model: ChatOpenAI,
    max_gleanings: int = 1,
    tuple_delimiter: str | None = None,
    record_delimiter: str | None = None,
    completion_delimiter: str | None = None,
    extraction_prompt: str | None = None,
) -> ExtractionResult:
    extractor = GraphExtractor(
        chat_model=chat_model, prompt=extraction_prompt, max_gleanings=max_gleanings
    )
    text_list = [unit.text.strip() for unit in units]

    results = await extractor(
        texts=text_list,
        prompt_variables={
            "entity_types": entity_types,
            "tuple_delimiter": tuple_delimiter,
            "record_delimiter": record_delimiter,
            "completion_delimiter": completion_delimiter,
        },
    )

    graph = results.output
    # Map the "source_id" back to the "id" field
    for _, node in graph.nodes(data=True):
        if node:
            node["source_id"] = ",".join(
                units[int(id)].id for id in node["source_id"].split(",")
            )
    for _, _, edge in graph.edges(data=True):
        if edge:
            edge["source_id"] = ",".join(
                units[int(id)].id for id in edge["source_id"].split(",")
            )

    entities: list[dict[str, Any]] = [
        {"title": node_item[0], **(node_item[1] or {})}
        for node_item in graph.nodes(data=True)
        if node_item
    ]
    relationships = to_polars_edgelist(graph)
    return ExtractionResult(pl.LazyFrame(entities), pl.LazyFrame(relationships), graph)
