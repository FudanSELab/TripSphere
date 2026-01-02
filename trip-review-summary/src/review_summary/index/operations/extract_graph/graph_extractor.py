# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'GraphExtractionResult' and 'GraphExtractor' models."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import networkx as nx
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI

from review_summary.prompts.index.extract_graph import (
    CONTINUE_PROMPT,
    GRAPH_EXTRACTION_PROMPT,
    LOOP_PROMPT,
)
from review_summary.utils.string import clean_str

DEFAULT_TUPLE_DELIMITER = "<|>"
DEFAULT_RECORD_DELIMITER = "##"
DEFAULT_COMPLETION_DELIMITER = "<|COMPLETE|>"

logger = logging.getLogger(__name__)


@dataclass
class GraphExtractionResult:
    """Unipartite graph extraction result class definition."""

    output: nx.Graph[str]
    source_docs: dict[Any, Any]


class GraphExtractor:
    """Unipartite graph extractor class definition."""

    def __init__(
        self,
        chat_model: ChatOpenAI,
        tuple_delimiter_key: str | None = None,
        record_delimiter_key: str | None = None,
        input_text_key: str | None = None,
        entity_types_key: str | None = None,
        completion_delimiter_key: str | None = None,
        prompt: str | None = None,
        join_descriptions: bool = True,
        max_gleanings: int | None = None,
    ):
        """Init method definition."""
        self._model = chat_model
        self._join_descriptions = join_descriptions
        self._input_text_key = input_text_key or "input_text"
        self._tuple_delimiter_key = tuple_delimiter_key or "tuple_delimiter"
        self._record_delimiter_key = record_delimiter_key or "record_delimiter"
        self._completion_delimiter_key = (
            completion_delimiter_key or "completion_delimiter"
        )
        self._entity_types_key = entity_types_key or "entity_types"
        self._extraction_prompt = prompt or GRAPH_EXTRACTION_PROMPT
        self._max_gleanings = max_gleanings if max_gleanings is not None else 1

    async def __call__(
        self, texts: list[str], prompt_variables: dict[str, Any] | None = None
    ) -> GraphExtractionResult:
        """Call method definition."""
        if prompt_variables is None:
            prompt_variables = {}
        all_records: dict[int, str] = {}
        source_doc_map: dict[int, str] = {}

        # Wire defaults into the prompt variables
        prompt_variables = {
            **prompt_variables,
            self._tuple_delimiter_key: prompt_variables.get(self._tuple_delimiter_key)
            or DEFAULT_TUPLE_DELIMITER,
            self._record_delimiter_key: prompt_variables.get(self._record_delimiter_key)
            or DEFAULT_RECORD_DELIMITER,
            self._completion_delimiter_key: prompt_variables.get(
                self._completion_delimiter_key
            )
            or DEFAULT_COMPLETION_DELIMITER,
            self._entity_types_key: ",".join(prompt_variables[self._entity_types_key]),
        }

        for doc_index, text in enumerate(texts):
            try:
                # Invoke the entity extraction
                result = await self._process_document(text, prompt_variables)
                source_doc_map[doc_index] = text
                all_records[doc_index] = result
            except Exception as e:
                logger.exception("error extracting graph", exc_info=e)

        output = await self._process_results(
            all_records,
            prompt_variables.get(self._tuple_delimiter_key, DEFAULT_TUPLE_DELIMITER),
            prompt_variables.get(self._record_delimiter_key, DEFAULT_RECORD_DELIMITER),
        )

        return GraphExtractionResult(
            output=output,
            source_docs=source_doc_map,
        )

    async def _process_document(
        self, text: str, prompt_variables: dict[str, str]
    ) -> str:
        history: list[BaseMessage] = [
            HumanMessage(
                self._extraction_prompt.format(
                    **{**prompt_variables, self._input_text_key: text}
                ),
            )
        ]
        response = await self._model.ainvoke(history)
        history.append(response)
        results = response.text or ""

        # if gleanings are specified, enter a loop to extract more entities
        # there are two exit criteria:
        #   (a) we hit the configured max
        #   (b) the model says there are no more entities
        if self._max_gleanings > 0:
            for i in range(self._max_gleanings):
                history.append(HumanMessage(CONTINUE_PROMPT))
                response = await self._model.ainvoke(history)
                history.append(response)
                results += response.text or ""

                # if this is the final glean, just break
                if i >= self._max_gleanings - 1:
                    break

                history.append(HumanMessage(LOOP_PROMPT))
                response = await self._model.ainvoke(history)
                history.append(response)
                if response.text != "Y":
                    break

        return results

    async def _process_results(
        self,
        results: dict[int, str],
        tuple_delimiter: str,
        record_delimiter: str,
    ) -> nx.Graph[str]:
        """Parse the result string to create an undirected unipartite graph.

        Arguments:
            results: dict of results from the extraction chain
            tuple_delimiter: delimiter between tuples in an output record,
                default is '<|>'
            record_delimiter: delimiter between records, default is '##'

        Returns:
            unipartite graph in graphML format
        """
        graph: nx.Graph[str] = nx.Graph()
        for source_doc_id, extracted_data in results.items():
            records = [r.strip() for r in extracted_data.split(record_delimiter)]

            for record in records:
                record = re.sub(r"^\(|\)$", "", record.strip())
                record_attributes = record.split(tuple_delimiter)

                if record_attributes[0] == '"entity"' and len(record_attributes) >= 4:
                    # add this record as a node in the G
                    entity_name = clean_str(record_attributes[1].upper())
                    entity_type = clean_str(record_attributes[2].upper())
                    entity_description = clean_str(record_attributes[3])

                    if entity_name in graph.nodes():
                        node = graph.nodes[entity_name]
                        if self._join_descriptions:
                            node["description"] = "\n".join(
                                list(
                                    {
                                        *_unpack_descriptions(node),
                                        entity_description,
                                    }
                                )
                            )
                        else:
                            if len(entity_description) > len(node["description"]):
                                node["description"] = entity_description
                        node["source_id"] = ", ".join(
                            list(
                                {
                                    *_unpack_source_ids(node),
                                    str(source_doc_id),
                                }
                            )
                        )
                        node["type"] = (
                            entity_type if entity_type != "" else node["type"]
                        )
                    else:
                        graph.add_node(
                            entity_name,
                            type=entity_type,
                            description=entity_description,
                            source_id=str(source_doc_id),
                        )

                if (
                    record_attributes[0] == '"relationship"'
                    and len(record_attributes) >= 5
                ):
                    # add this record as edge
                    source = clean_str(record_attributes[1].upper())
                    target = clean_str(record_attributes[2].upper())
                    edge_description = clean_str(record_attributes[3])
                    edge_source_id = clean_str(str(source_doc_id))
                    try:
                        weight = float(record_attributes[-1])
                    except ValueError:
                        weight = 1.0

                    if source not in graph.nodes():
                        graph.add_node(
                            source,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if target not in graph.nodes():
                        graph.add_node(
                            target,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if graph.has_edge(source, target):
                        edge_data = graph.get_edge_data(source, target)
                        if edge_data:
                            weight += edge_data["weight"]
                            if self._join_descriptions:
                                edge_description = "\n".join(
                                    list(
                                        {
                                            *_unpack_descriptions(edge_data),
                                            edge_description,
                                        }
                                    )
                                )
                            edge_source_id = ", ".join(
                                list(
                                    {
                                        *_unpack_source_ids(edge_data),
                                        str(source_doc_id),
                                    }
                                )
                            )
                    graph.add_edge(
                        source,
                        target,
                        weight=weight,
                        description=edge_description,
                        source_id=edge_source_id,
                    )

        return graph


def _unpack_descriptions(data: dict[str, Any]) -> list[str]:
    value = data.get("description", None)
    return [] if value is None else value.split("\n")


def _unpack_source_ids(data: dict[str, Any]) -> list[str]:
    value = data.get("source_id", None)
    return [] if value is None else value.split(", ")
