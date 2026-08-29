import asyncio
import logging

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from neo4j import AsyncDriver
from qdrant_client import AsyncQdrantClient
from tiktoken import encoding_name_for_model

from review_summary.clients.reviews import ReviewServiceClient, TargetType
from review_summary.config.settings import get_settings
from review_summary.infra.nacos.naming import NacosNaming
from review_summary.query.base import SearchResult
from review_summary.query.review_state import (
    ReviewDependencyError,
    ReviewIndexPreflight,
    ReviewPreflightResult,
    ReviewState,
    evidence_from_context,
)
from review_summary.query.structured_search.local_search.mixed_content import (
    LocalSearchMixedContext,
)
from review_summary.query.structured_search.local_search.search import LocalSearch
from review_summary.tokenizer.tiktoken import TiktokenTokenizer
from review_summary.vector_stores.entity import EntityVectorStore
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)


class ReviewSummaryService:
    CHAT_MODEL = "gpt-4o-mini"
    CHAT_TEMPERATURE = 0.0
    EMBEDDING_MODEL = "text-embedding-3-large"

    def __init__(
        self,
        neo4j_driver: AsyncDriver,
        qdrant_client: AsyncQdrantClient,
        nacos_naming: NacosNaming,
    ) -> None:
        self.neo4j_driver = neo4j_driver
        self.qdrant_client = qdrant_client
        self.review_client = ReviewServiceClient(nacos_naming)
        self.openai_settings = get_settings().openai
        self._chat_model: ChatOpenAI | None = None
        self._embedding_model: OpenAIEmbeddings | None = None
        self._tokenizer: TiktokenTokenizer | None = None
        self._search_engine: LocalSearch | None = None
        self._entity_vector_store: EntityVectorStore | None = None
        self._text_unit_vector_store: TextUnitVectorStore | None = None

    async def summarize(
        self,
        query: str,
        target_id: str,
        target_type: TargetType,
    ) -> ReviewState:
        query = query.strip()
        target_id = target_id.strip()
        if not query:
            raise ValueError("query must not be empty")
        if not target_id:
            raise ValueError("target_id must not be empty")

        try:
            preflight = await self._run_preflight(target_id, target_type)
        except ReviewDependencyError as error:
            logger.exception("Review index dependency failure")
            return self._dependency_failure(
                target_id,
                target_type,
                error,
                "评论分析依赖暂时不可用，请稍后重试。",
            )

        if preflight.status != "ready":
            return ReviewState(
                status=preflight.status,
                target_id=target_id,
                target_type=target_type,
                review_snapshot=preflight.snapshot,
                message=preflight.message,
            )

        try:
            result = await self._execute_search(
                query,
                target_id,
                target_type,
                preflight.snapshot,
            )
            return await self._complete_search(
                result,
                target_id,
                target_type,
                preflight,
            )
        except ReviewDependencyError as error:
            logger.exception("Review index dependency failure after search")
            return self._dependency_failure(
                target_id,
                target_type,
                error,
                "评论分析依赖暂时不可用，请稍后重试。",
                preflight.snapshot,
            )
        except Exception:
            logger.exception("Review analysis dependency failure")
            return ReviewState(
                status="dependency_failure",
                target_id=target_id,
                target_type=target_type,
                review_snapshot=preflight.snapshot,
                message="评论分析暂时不可用，请稍后重试。",
                dependency="review_analysis",
                error_code="REVIEW_ANALYSIS_FAILED",
            )

    async def _complete_search(
        self,
        result: SearchResult,
        target_id: str,
        target_type: TargetType,
        preflight: ReviewPreflightResult,
    ) -> ReviewState:
        postflight = await self._run_preflight(target_id, target_type)
        if postflight.status != "ready":
            return ReviewState(
                status=postflight.status,
                target_id=target_id,
                target_type=target_type,
                review_snapshot=postflight.snapshot,
                message=postflight.message,
            )
        if postflight.snapshot != preflight.snapshot:
            return ReviewState(
                status="index_missing",
                target_id=target_id,
                target_type=target_type,
                review_snapshot=postflight.snapshot,
                message="评论在回答生成期间发生变化，请刷新索引后重试。",
            )

        evidence = evidence_from_context(result.context_data)
        if not evidence:
            return ReviewState(
                status="index_missing",
                target_id=target_id,
                target_type=target_type,
                review_snapshot=preflight.snapshot,
                message="评论索引中没有可用于回答的来源证据。",
            )
        if not isinstance(result.response, str) or not result.response.strip():
            raise RuntimeError("Review analysis returned no answer")

        return ReviewState(
            status="success",
            target_id=target_id,
            target_type=target_type,
            review_snapshot=preflight.snapshot,
            answer=result.response,
            evidence=evidence,
        )

    async def _init_vector_stores(
        self,
    ) -> tuple[EntityVectorStore, TextUnitVectorStore]:
        if self._entity_vector_store and self._text_unit_vector_store:
            return self._entity_vector_store, self._text_unit_vector_store

        entity_vector_store, text_unit_vector_store = await asyncio.gather(
            EntityVectorStore.create_vector_store(client=self.qdrant_client),
            TextUnitVectorStore.create_vector_store(client=self.qdrant_client),
        )
        self._entity_vector_store = entity_vector_store
        self._text_unit_vector_store = text_unit_vector_store
        return entity_vector_store, text_unit_vector_store

    def _get_chat_model(self) -> ChatOpenAI:
        if self._chat_model is None:
            self._chat_model = ChatOpenAI(
                model=self.CHAT_MODEL,
                temperature=self.CHAT_TEMPERATURE,
                api_key=self.openai_settings.api_key,
                base_url=self.openai_settings.base_url,
            )
        return self._chat_model

    def _get_embedding_model(self) -> OpenAIEmbeddings:
        if self._embedding_model is None:
            self._embedding_model = OpenAIEmbeddings(
                model=self.EMBEDDING_MODEL,
                api_key=self.openai_settings.api_key,
                base_url=self.openai_settings.base_url,
            )
        return self._embedding_model

    def _get_tokenizer(self) -> TiktokenTokenizer:
        if self._tokenizer is None:
            encoding_name = encoding_name_for_model(self._get_chat_model().model_name)
            self._tokenizer = TiktokenTokenizer(encoding_name)
        return self._tokenizer

    async def _init_search_engine(self) -> LocalSearch:
        if self._search_engine is None:
            entity_vector_store, text_unit_vector_store = (
                await self._init_vector_stores()
            )
            tokenizer = self._get_tokenizer()
            self._search_engine = LocalSearch(
                chat_model=self._get_chat_model(),
                context_builder=LocalSearchMixedContext(
                    entity_vector_store=entity_vector_store,
                    text_unit_vector_store=text_unit_vector_store,
                    embedding_model=self._get_embedding_model(),
                    tokenizer=tokenizer,
                    neo4j_driver=self.neo4j_driver,
                ),
                tokenizer=tokenizer,
            )
        return self._search_engine

    async def _execute_search(
        self,
        query: str,
        target_id: str,
        target_type: TargetType,
        review_snapshot: str,
    ) -> SearchResult:
        search = await self._init_search_engine()
        logger.info(
            "Executing review search for target_id=%s target_type=%s",
            target_id,
            target_type.value,
        )
        return await search.search(
            query=query,
            target_id=target_id,
            target_type=target_type.value,
            review_snapshot=review_snapshot,
        )

    async def _run_preflight(
        self,
        target_id: str,
        target_type: TargetType,
    ) -> ReviewPreflightResult:
        try:
            entity_store, text_unit_store = await self._init_vector_stores()
        except Exception as exc:
            raise ReviewDependencyError(
                "qdrant",
                "QDRANT_UNAVAILABLE",
                "Unable to initialize the review vector index",
            ) from exc

        return await ReviewIndexPreflight(
            review_client=self.review_client,
            text_unit_store=text_unit_store,
            entity_store=entity_store,
            neo4j_driver=self.neo4j_driver,
        ).run(target_id, target_type)

    @staticmethod
    def _dependency_failure(
        target_id: str,
        target_type: TargetType,
        error: ReviewDependencyError,
        message: str,
        review_snapshot: str | None = None,
    ) -> ReviewState:
        return ReviewState(
            status="dependency_failure",
            target_id=target_id,
            target_type=target_type,
            review_snapshot=review_snapshot,
            message=message,
            dependency=error.dependency,
            error_code=error.error_code,
        )
