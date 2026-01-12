import logging
from copy import deepcopy

import pandas as pd
from langchain_openai import OpenAIEmbeddings
from neo4j import AsyncDriver

from review_summary.models import CommunityReport, Entity, Relationship, TextUnit
from review_summary.query.context_builder.builders import ContextBuilderResult
from review_summary.query.context_builder.community_context import (
    build_community_context,
)
from review_summary.query.context_builder.conversation_history import (
    ConversationHistory,
)
from review_summary.query.context_builder.local_context import (
    build_entity_context,
    build_relationship_context,
)
from review_summary.query.context_builder.source_context import (
    build_text_unit_context,
    count_relationships,
)
from review_summary.query.fetch_data.fetch_relationship import (
    fetch_relationships_for_entities,
)
from review_summary.tokenizer.tokenizer import Tokenizer
from review_summary.vector_stores.entity import EntityVectorStore
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)


class LocalSearchMixedContext:
    """Build data context for local search prompt combining community
    reports and entity/relationship/covariate tables."""

    def __init__(
        self,
        entity_text_embeddings: EntityVectorStore,
        text_unit_store: TextUnitVectorStore,
        text_embedder: OpenAIEmbeddings,
        tokenizer: Tokenizer,
        neo4j_driver: AsyncDriver,
        community_reports: list[CommunityReport] | None = None,
    ):
        if community_reports is None:
            community_reports = []
        self.community_reports = {
            community.community_id: community for community in community_reports
        }
        self.entity_text_embeddings = entity_text_embeddings
        self.text_embedder = text_embedder
        self.tokenizer = tokenizer
        self.neo4j_driver = neo4j_driver
        self.text_unit_store = text_unit_store

    async def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        include_entity_names: list[str] | None = None,
        exclude_entity_names: list[str] | None = None,
        conversation_history_max_turns: int | None = 5,
        conversation_history_user_turns_only: bool = True,
        max_context_tokens: int = 8000,
        text_unit_prop: float = 0.5,
        community_prop: float = 0,
        top_k_mapped_entities: int = 10,
        top_k_relationships: int = 10,
        include_community_rank: bool = False,
        include_entity_rank: bool = False,
        rank_description: str = "number of relationships",
        include_relationship_weight: bool = False,
        relationship_ranking_attribute: str = "rank",
        use_community_summary: bool = False,
        min_community_rank: int = 0,
        community_context_name: str = "Reports",
        column_delimiter: str = "|",
        target_id: str = "",
    ) -> ContextBuilderResult:
        """
        Build data context for local search prompt.

        Build a context by combining community reports
        and entity/relationship/covariate tables,
        and text units using a predefined ratio set by summary_prop.
        """
        if include_entity_names is None:
            include_entity_names = []
        if exclude_entity_names is None:
            exclude_entity_names = []
        if community_prop + text_unit_prop > 1:
            value_error = (
                "The sum of community_prop and text_unit_prop should not exceed 1."
            )
            raise ValueError(value_error)

        # map user query to entities
        # if there is conversation history, attached the previous
        # user questions to the current query
        if conversation_history:
            pre_user_questions = "\n".join(
                conversation_history.get_user_turns(conversation_history_max_turns)
            )
            query = f"{query}\n{pre_user_questions}"

        query_embedding = await self.text_embedder.aembed_query(query)
        selected_entities = await self.entity_text_embeddings.search_by_vector(
            embedding_vector=query_embedding,
            top_k=top_k_mapped_entities,
            target_id=target_id,
        )
        # get relationships
        relationships: list[Relationship] = []
        relationships = await fetch_relationships_for_entities(
            driver=self.neo4j_driver, entities=selected_entities
        )
        # get text_units
        text_units: list[TextUnit] = []
        text_units = await self.text_unit_store.find_by_target(target_id=target_id)

        # build context
        final_context = list[str]()
        final_context_data = dict[str, pd.DataFrame]()

        if conversation_history:
            # build conversation history context
            (
                conversation_history_context,
                conversation_history_context_data,
            ) = conversation_history.build_context(
                tokenizer=self.tokenizer,
                include_user_turns_only=conversation_history_user_turns_only,
                max_qa_turns=conversation_history_max_turns,
                column_delimiter=column_delimiter,
                max_context_tokens=max_context_tokens,
                recency_bias=False,
            )
            if conversation_history_context.strip() != "":
                final_context.append(conversation_history_context)
                final_context_data = conversation_history_context_data
                max_context_tokens = max_context_tokens - len(
                    self.tokenizer.encode(conversation_history_context)
                )

        # build community context
        community_tokens = max(int(max_context_tokens * community_prop), 0)
        community_context, community_context_data = self._build_community_context(
            selected_entities=selected_entities,
            max_context_tokens=community_tokens,
            use_community_summary=use_community_summary,
            column_delimiter=column_delimiter,
            include_community_rank=include_community_rank,
            min_community_rank=min_community_rank,
            context_name=community_context_name,
        )
        if community_context.strip() != "":
            final_context.append(community_context)
            final_context_data = {**final_context_data, **community_context_data}

        # build local (i.e. entity-relationship-covariate) context
        local_prop = 1 - community_prop - text_unit_prop
        local_tokens = max(int(max_context_tokens * local_prop), 0)
        local_context, local_context_data = self._build_local_context(
            selected_entities=selected_entities,
            max_context_tokens=local_tokens,
            include_entity_rank=include_entity_rank,
            rank_description=rank_description,
            include_relationship_weight=include_relationship_weight,
            top_k_relationships=top_k_relationships,
            relationship_ranking_attribute=relationship_ranking_attribute,
            column_delimiter=column_delimiter,
            relationships=relationships,
        )
        if local_context.strip() != "":
            final_context.append(str(local_context))
            final_context_data = {**final_context_data, **local_context_data}

        text_unit_tokens = max(int(max_context_tokens * text_unit_prop), 0)
        text_unit_context, text_unit_context_data = self._build_text_unit_context(
            selected_entities=selected_entities,
            max_context_tokens=text_unit_tokens,
            text_units=text_units,
            relationships=relationships,
        )

        if text_unit_context.strip() != "":
            final_context.append(text_unit_context)
            final_context_data = {**final_context_data, **text_unit_context_data}

        return ContextBuilderResult(
            context_chunks="\n\n".join(final_context),
            context_records=final_context_data,
        )

    def _build_community_context(
        self,
        selected_entities: list[Entity],
        max_context_tokens: int = 4000,
        use_community_summary: bool = False,
        column_delimiter: str = "|",
        include_community_rank: bool = False,
        min_community_rank: int = 0,
        context_name: str = "Reports",
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """Add community data to the context window until
        it hits the max_context_tokens limit."""
        if len(selected_entities) == 0 or len(self.community_reports) == 0:
            return ("", {context_name.lower(): pd.DataFrame()})

        community_matches: dict[str, int] = {}
        for entity in selected_entities:
            # increase count of the community that this entity belongs to
            if entity.community_ids:
                for community_id in entity.community_ids:
                    community_matches[community_id] = (
                        community_matches.get(community_id, 0) + 1  # pyright: ignore
                    )

        # sort communities by number of matched entities and rank
        selected_communities = [
            self.community_reports[community_id]
            for community_id in community_matches  # pyright: ignore
            if community_id in self.community_reports
        ]
        for community in selected_communities:
            if community.attributes is None:
                community.attributes = {}
            community.attributes["matches"] = community_matches[community.community_id]
        selected_communities.sort(
            key=lambda x: (x.attributes["matches"], x.rank),  # type: ignore
            reverse=True,
        )
        for community in selected_communities:
            del community.attributes["matches"]  # type: ignore

        context_text, context_data = build_community_context(
            community_reports=selected_communities,
            tokenizer=self.tokenizer,
            use_community_summary=use_community_summary,
            column_delimiter=column_delimiter,
            shuffle_data=False,
            include_community_rank=include_community_rank,
            min_community_rank=min_community_rank,
            max_context_tokens=max_context_tokens,
            single_batch=True,
            context_name=context_name,
        )
        if isinstance(context_text, list) and len(context_text) > 0:
            context_text = "\n\n".join(context_text)

        return (str(context_text), context_data)

    def _build_text_unit_context(
        self,
        selected_entities: list[Entity],
        text_units: list[TextUnit],
        relationships: list[Relationship],
        max_context_tokens: int = 8000,
        column_delimiter: str = "|",
        context_name: str = "Sources",
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """Rank matching text units and add them to the context
        window until it hits the max_context_tokens limit."""
        if not selected_entities or not text_units:
            return ("", {context_name.lower(): pd.DataFrame()})
        selected_text_units = []
        text_unit_ids_set: set[str] = set()
        unit_info_list: list[tuple[TextUnit, int, int]] = []
        text_units_dict = {tu.id: tu for tu in text_units}

        for index, entity in enumerate(selected_entities):
            # get matching relationships
            entity_relationships = [
                rel
                for rel in relationships
                if rel.source == entity.title or rel.target == entity.title
            ]

            for text_id in entity.text_unit_ids or []:
                if text_id not in text_unit_ids_set and text_id in text_units_dict:
                    selected_unit = deepcopy(text_units_dict[text_id])
                    num_relationships = count_relationships(
                        entity_relationships, selected_unit
                    )
                    text_unit_ids_set.add(text_id)
                    unit_info_list.append((selected_unit, index, num_relationships))

        # sort by entity_order and the number of relationships desc
        unit_info_list.sort(key=lambda x: (x[1], -x[2]))

        selected_text_units = [unit[0] for unit in unit_info_list]

        context_text, context_data = build_text_unit_context(
            text_units=selected_text_units,
            tokenizer=self.tokenizer,
            max_context_tokens=max_context_tokens,
            shuffle_data=False,
            context_name=context_name,
            column_delimiter=column_delimiter,
        )
        return (str(context_text), context_data)

    def _build_local_context(
        self,
        selected_entities: list[Entity],
        relationships: list[Relationship],
        max_context_tokens: int = 8000,
        include_entity_rank: bool = False,
        rank_description: str = "relationship count",
        include_relationship_weight: bool = False,
        top_k_relationships: int = 10,
        relationship_ranking_attribute: str = "rank",
        column_delimiter: str = "|",
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """Build data context for local search prompt
        combining entity/relationship/covariate tables."""
        # build entity context
        entity_context, entity_context_data = build_entity_context(
            selected_entities=selected_entities,
            tokenizer=self.tokenizer,
            max_context_tokens=max_context_tokens,
            column_delimiter=column_delimiter,
            include_entity_rank=include_entity_rank,
            rank_description=rank_description,
            context_name="Entities",
        )
        entity_tokens = len(self.tokenizer.encode(entity_context))

        # build relationship-covariate context
        added_entities: list[Entity] = []
        final_context = []
        final_context_data = {}

        # gradually add entities and associated
        # metadata to the context until we reach limit
        for entity in selected_entities:
            current_context: list[str] = []
            current_context_data: dict[str, pd.DataFrame] = {}
            added_entities.append(entity)

            # build relationship context
            (
                relationship_context,
                relationship_context_data,
            ) = build_relationship_context(
                selected_entities=added_entities,
                relationships=relationships,
                tokenizer=self.tokenizer,
                max_context_tokens=max_context_tokens,
                column_delimiter=column_delimiter,
                top_k_relationships=top_k_relationships,
                include_relationship_weight=include_relationship_weight,
                relationship_ranking_attribute=relationship_ranking_attribute,
                context_name="Relationships",
            )
            current_context.append(relationship_context)
            current_context_data["relationships"] = relationship_context_data
            total_tokens = entity_tokens + len(
                self.tokenizer.encode(relationship_context)
            )

            if total_tokens > max_context_tokens:
                logger.warning(
                    "Reached token limit - reverting to previous context state"
                )
                break

            final_context = current_context
            final_context_data = current_context_data

        # attach entity context to final context
        final_context_text = entity_context + "\n\n" + "\n\n".join(final_context)
        final_context_data["entities"] = entity_context_data
        return (final_context_text, final_context_data)
