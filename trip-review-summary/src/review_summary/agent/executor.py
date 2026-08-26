import asyncio
import logging
from typing import Any

import a2a.types
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.utils import new_agent_text_message, new_task
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


class A2aAgentExecutor(AgentExecutor):
    # Model configuration constants
    CHAT_MODEL = "gpt-4o-mini"
    CHAT_TEMPERATURE = 0.0
    EMBEDDING_MODEL = "text-embedding-3-large"

    def __init__(
        self,
        neo4j_driver: AsyncDriver,
        qdrant_client: AsyncQdrantClient,
        nacos_naming: NacosNaming,
    ) -> None:
        """Initialize the agent executor with required clients.

        Arguments:
            neo4j_driver: Async Neo4j driver for graph database operations
            qdrant_client: Async Qdrant client for vector store operations
        """
        self.neo4j_driver = neo4j_driver
        self.qdrant_client = qdrant_client
        self.review_client = ReviewServiceClient(nacos_naming)

        # Cache settings to avoid repeated calls
        self.openai_settings = get_settings().openai

        # Initialize core components (lazy initialization on first use)
        # These are cached across requests for better performance
        self._chat_model: ChatOpenAI | None = None
        self._embedding_model: OpenAIEmbeddings | None = None
        self._tokenizer: TiktokenTokenizer | None = None
        self._search_engine: LocalSearch | None = None
        self._entity_vector_store: EntityVectorStore | None = None
        self._text_unit_vector_store: TextUnitVectorStore | None = None

        logger.info("A2aAgentExecutor initialized successfully")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the review summary agent workflow."""
        task = await self._ensure_task(context, event_queue)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            query, target_id, target_type = self._validate_context(context)
        except Exception as error:
            await self._handle_error(error, updater)
            return

        try:
            preflight = await self._run_preflight(
                target_id,
                target_type,
                updater,
            )
        except ReviewDependencyError as error:
            logger.error(
                "Review index dependency failure: %s",
                error,
                exc_info=True,
            )
            await self._emit_state(
                ReviewState(
                    status="dependency_failure",
                    target_id=target_id,
                    target_type=target_type,
                    message="评论分析依赖暂时不可用，请稍后重试。",
                    dependency=error.dependency,
                    error_code=error.error_code,
                ),
                updater,
            )
            return

        if preflight.status != "ready":
            await self._emit_state(
                ReviewState(
                    status=preflight.status,
                    target_id=target_id,
                    target_type=target_type,
                    review_snapshot=preflight.snapshot,
                    message=preflight.message,
                ),
                updater,
            )
            return

        try:
            result = await self._execute_search(
                query,
                target_id,
                target_type,
                preflight.snapshot,
                updater,
            )

            postflight = await self._run_preflight(
                target_id,
                target_type,
                updater,
            )
            if postflight.status != "ready":
                await self._emit_state(
                    ReviewState(
                        status=postflight.status,
                        target_id=target_id,
                        target_type=target_type,
                        review_snapshot=postflight.snapshot,
                        message=postflight.message,
                    ),
                    updater,
                )
                return
            if postflight.snapshot != preflight.snapshot:
                await self._emit_state(
                    ReviewState(
                        status="index_missing",
                        target_id=target_id,
                        target_type=target_type,
                        review_snapshot=postflight.snapshot,
                        message=(
                            "评论在回答生成期间发生变化，"
                            "请刷新索引后重试。"
                        ),
                    ),
                    updater,
                )
                return

            evidence = evidence_from_context(result.context_data)
            if not evidence:
                await self._emit_state(
                    ReviewState(
                        status="index_missing",
                        target_id=target_id,
                        target_type=target_type,
                        review_snapshot=preflight.snapshot,
                        message="评论索引中没有可用于回答的来源证据。",
                    ),
                    updater,
                )
                return

            if not isinstance(result.response, str) or not result.response.strip():
                raise RuntimeError("Review analysis returned no answer")
            await self._emit_state(
                ReviewState(
                    status="success",
                    target_id=target_id,
                    target_type=target_type,
                    review_snapshot=preflight.snapshot,
                    answer=result.response,
                    evidence=evidence,
                ),
                updater,
                result,
            )
        except ReviewDependencyError as error:
            logger.error(
                "Review index dependency failure after search: %s",
                error,
                exc_info=True,
            )
            await self._emit_state(
                ReviewState(
                    status="dependency_failure",
                    target_id=target_id,
                    target_type=target_type,
                    review_snapshot=preflight.snapshot,
                    message="评论分析依赖暂时不可用，请稍后重试。",
                    dependency=error.dependency,
                    error_code=error.error_code,
                ),
                updater,
            )
        except Exception:
            logger.error("Review analysis dependency failure", exc_info=True)
            await self._emit_state(
                ReviewState(
                    status="dependency_failure",
                    target_id=target_id,
                    target_type=target_type,
                    review_snapshot=preflight.snapshot,
                    message="评论分析暂时不可用，请稍后重试。",
                    dependency="review_analysis",
                    error_code="REVIEW_ANALYSIS_FAILED",
                ),
                updater,
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the current task execution."""
        task = context.current_task
        if task is None:
            logger.debug("No active task to cancel")
            return

        logger.info(f"Cancelling task {task.id}")
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.update_status(
            a2a.types.TaskState.canceled,
            new_agent_text_message(
                "Review summary request cancelled", task.context_id, task.id
            ),
            final=True,
        )

    async def _init_vector_stores(
        self,
    ) -> tuple[EntityVectorStore, TextUnitVectorStore]:
        """Initialize vector stores concurrently."""
        if self._entity_vector_store and self._text_unit_vector_store:
            return self._entity_vector_store, self._text_unit_vector_store

        logger.debug("Initializing vector stores concurrently")
        entity_vector_store, text_unit_vector_store = await asyncio.gather(
            EntityVectorStore.create_vector_store(client=self.qdrant_client),
            TextUnitVectorStore.create_vector_store(client=self.qdrant_client),
        )
        self._entity_vector_store = entity_vector_store
        self._text_unit_vector_store = text_unit_vector_store
        logger.debug("Vector stores are initialized successfully")
        return entity_vector_store, text_unit_vector_store

    def _get_chat_model(self) -> ChatOpenAI:
        """Get or create the chat model instance (lazy initialization)."""
        if self._chat_model is None:
            logger.debug(f"Initializing ChatOpenAI with model: {self.CHAT_MODEL}")
            self._chat_model = ChatOpenAI(
                model=self.CHAT_MODEL,
                temperature=self.CHAT_TEMPERATURE,
                api_key=self.openai_settings.api_key,
                base_url=self.openai_settings.base_url,
            )
        return self._chat_model

    def _get_embedding_model(self) -> OpenAIEmbeddings:
        """Get or create the embedding_model instance (lazy initialization)."""
        if self._embedding_model is None:
            logger.debug(
                f"Initializing OpenAIEmbeddings with model: {self.EMBEDDING_MODEL}"
            )
            self._embedding_model = OpenAIEmbeddings(
                model=self.EMBEDDING_MODEL,
                api_key=self.openai_settings.api_key,
                base_url=self.openai_settings.base_url,
            )
        return self._embedding_model

    def _get_tokenizer(self) -> TiktokenTokenizer:
        """Get or create the tokenizer instance (lazy initialization)."""
        if self._tokenizer is None:
            chat_model = self._get_chat_model()
            encoding_name = encoding_name_for_model(chat_model.model_name)
            logger.debug(
                f"Initializing TiktokenTokenizer with encoding_name: {encoding_name}"
            )
            self._tokenizer = TiktokenTokenizer(encoding_name)
        return self._tokenizer

    async def _init_search_engine(self) -> LocalSearch:
        """Initialize or get the cached search engine with all dependencies."""
        if self._search_engine is None:
            logger.debug("Initializing LocalSearch with all dependencies")

            # Initialize vector stores concurrently
            (
                entity_vector_store,
                text_unit_vector_store,
            ) = await self._init_vector_stores()

            # Get cached model instances (reused across requests for efficiency)
            chat_model = self._get_chat_model()
            embedding_model = self._get_embedding_model()
            tokenizer = self._get_tokenizer()

            # Build context builder
            context_builder = LocalSearchMixedContext(
                entity_vector_store=entity_vector_store,
                text_unit_vector_store=text_unit_vector_store,
                embedding_model=embedding_model,
                tokenizer=tokenizer,
                neo4j_driver=self.neo4j_driver,
            )

            # Initialize search and cache it
            self._search_engine = LocalSearch(
                chat_model=chat_model,
                context_builder=context_builder,
                tokenizer=tokenizer,
            )
            logger.debug("LocalSearch initialized and cached successfully")
        else:
            logger.debug("Using cached LocalSearch instance")

        return self._search_engine

    def _validate_context(
        self, context: RequestContext
    ) -> tuple[str, str, TargetType]:
        """Validate and extract required information from request context.

        Arguments:
            context: The request context to validate

        Returns:
            Tuple of (query, target_id, target_type)

        Raises:
            ValueError: If query or authoritative target metadata is invalid
        """
        query = context.get_user_input().strip()
        if not query:
            raise ValueError("query must not be empty")

        metadata = context.metadata or {}
        raw_target_id = metadata.get("target_id")
        raw_target_type = metadata.get("target_type")
        if not isinstance(raw_target_id, str) or not raw_target_id.strip():
            raise ValueError("target_id is missing from request metadata")
        if not isinstance(raw_target_type, str):
            raise ValueError("target_type is missing from request metadata")

        target_id = raw_target_id.strip()
        try:
            target_type = TargetType(raw_target_type.strip().lower())
        except ValueError as exc:
            raise ValueError(
                "target_type must be hotel or attraction"
            ) from exc

        logger.debug(
            "Context validated - query length: %s, target_id: %s, target_type: %s",
            len(query),
            target_id,
            target_type.value,
        )
        return query, target_id, target_type

    async def _ensure_task(
        self, context: RequestContext, event_queue: EventQueue
    ) -> a2a.types.Task:
        """Ensure a task exists for the current execution."""
        task = context.current_task
        if not task:
            task = new_task(context.message)  # type: ignore
            await event_queue.enqueue_event(task)
            logger.debug(f"Created new task with id: {task.id}")
        return task

    async def _execute_search(
        self,
        query: str,
        target_id: str,
        target_type: TargetType,
        review_snapshot: str,
        updater: TaskUpdater,
    ) -> SearchResult:
        """Execute the search operation with progress updates."""
        await updater.update_status(
            a2a.types.TaskState.working,
            new_agent_text_message(
                text="Collecting review evidence...",
                context_id=updater.context_id,
                task_id=updater.task_id,
            ),
        )

        # Initialize search engine
        search = await self._init_search_engine()

        await updater.update_status(
            a2a.types.TaskState.working,
            new_agent_text_message(
                "Searching indexed reviews...",
                updater.context_id,
                updater.task_id,
            ),
        )

        # Execute search
        logger.info(
            "Executing search for target_id=%s target_type=%s",
            target_id,
            target_type.value,
        )
        result = await search.search(
            query=query,
            target_id=target_id,
            target_type=target_type.value,
            review_snapshot=review_snapshot,
        )
        logger.info(
            f"Search completed - "
            f"tokens: {result.prompt_tokens + result.output_tokens}, "
            f"time: {result.completion_time:.2f}s"
        )
        return result

    async def _run_preflight(
        self,
        target_id: str,
        target_type: TargetType,
        updater: TaskUpdater,
    ) -> ReviewPreflightResult:
        await updater.update_status(
            a2a.types.TaskState.working,
            new_agent_text_message(
                "Checking the live review index...",
                updater.context_id,
                updater.task_id,
            ),
        )
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

    async def _emit_state(
        self,
        state: ReviewState,
        updater: TaskUpdater,
        result: SearchResult | None = None,
    ) -> None:
        metadata: dict[str, Any] = {}
        if result is not None:
            metadata = {
                "completion_time": result.completion_time,
                "llm_calls": result.llm_calls,
                "prompt_tokens": result.prompt_tokens,
                "output_tokens": result.output_tokens,
            }

        parts = [a2a.types.Part(root=a2a.types.DataPart(data=state.to_payload()))]
        await updater.add_artifact(parts=parts, metadata=metadata)
        await updater.complete()
        logger.info(
            "Task %s completed with review status %s",
            updater.task_id,
            state.status,
        )

    async def _handle_error(self, error: Exception, updater: TaskUpdater) -> None:
        """Handle execution errors with appropriate logging and user feedback."""

        error_msg = f"Error processing review summary: {str(error)}"

        # Enhanced logging with error categorization for debugging
        if isinstance(error, KeyError):
            logger.error(
                f"Missing required field in request: {str(error)}", exc_info=True
            )
        elif isinstance(error, (ConnectionError, TimeoutError)):
            logger.error(
                f"Connection error during execution: {str(error)}", exc_info=True
            )
        else:
            logger.error(error_msg, exc_info=True)

        # Send failure status with error message
        await updater.update_status(
            a2a.types.TaskState.failed,
            new_agent_text_message(error_msg, updater.context_id, updater.task_id),
            final=True,
        )
