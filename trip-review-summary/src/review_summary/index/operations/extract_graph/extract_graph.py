import asyncio
import logging
from typing import Any

import networkx as nx
import pandas as pd
from langchain_openai import ChatOpenAI

from review_summary.config.settings import get_settings
from review_summary.index.operations.extract_graph.graph_extractor import GraphExtractor
from review_summary.index.operations.extract_graph.typing import ExtractionResult, Unit

logger = logging.getLogger(__name__)


async def extract_graph(
    text_units: pd.DataFrame,
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
) -> tuple[pd.DataFrame, pd.DataFrame]:
    semaphore = asyncio.Semaphore(num_concurrency)

    # Initialize ChatOpenAI model with provided config
    openai_settings = get_settings().openai
    if "api_key" not in chat_model_config:
        chat_model_config["api_key"] = openai_settings.api_key
    if "base_url" not in chat_model_config:
        chat_model_config["base_url"] = openai_settings.base_url
    chat_model = ChatOpenAI(**chat_model_config)
    logger.debug("Initialized ChatOpenAI model for graph extraction.")

    async def _process_row(row: Any) -> ExtractionResult:
        async with semaphore:
            id = getattr(row, id_column)
            text = getattr(row, text_column)
            return await _run_graph_extraction(
                units=[Unit(id=id, text=text)],
                entity_types=entity_types,
                chat_model=chat_model,
                max_gleanings=max_gleanings,
                tuple_delimiter=tuple_delimiter,
                record_delimiter=record_delimiter,
                completion_delimiter=completion_delimiter,
                extraction_prompt=extraction_prompt,
            )

    text_units_df = text_units[[id_column, text_column]]
    # Gather all results concurrently with semaphore control
    results = await asyncio.gather(
        *[_process_row(row) for row in text_units_df.itertuples()]
    )

    entity_dfs: list[pd.DataFrame] = []
    relationship_dfs: list[pd.DataFrame] = []
    for result in results:
        entity_dfs.append(result.entities)
        relationship_dfs.append(result.relationships)
    # Merge all raw entity and raw relationship DataFrames
    logger.info("Merging extracted entities and relationships.")
    entities = _merge_entities(entity_dfs)
    relationships = _merge_relationships(relationship_dfs)
    return entities, relationships


def _merge_entities(entity_dfs: list[pd.DataFrame]) -> pd.DataFrame:
    all_entities = pd.concat(entity_dfs, ignore_index=True)
    return (
        all_entities.groupby(["title", "type"], sort=False)  # pyright: ignore
        .agg(
            description=("description", list),
            text_unit_ids=("source_id", list),
            frequency=("source_id", "count"),
        )
        .reset_index()
    )


def _merge_relationships(relationship_dfs: list[pd.DataFrame]) -> pd.DataFrame:
    all_relationships = pd.concat(relationship_dfs, ignore_index=False)
    return (
        all_relationships.groupby(["source", "target"], sort=False)  # pyright: ignore
        .agg(
            description=("description", list),
            text_unit_ids=("source_id", list),
            weight=("weight", "sum"),
        )
        .reset_index()
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
    logger.info("Mapping the 'source_id' back to the 'id' field")
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
    relationships = nx.to_pandas_edgelist(graph)  # ty: ignore
    return ExtractionResult(pd.DataFrame(entities), pd.DataFrame(relationships), graph)
