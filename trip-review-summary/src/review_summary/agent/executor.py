import asyncio
import logging
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import DataPart, Part, Task, TaskState, TextPart
from a2a.utils import new_agent_text_message, new_task
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from neo4j import AsyncDriver
from qdrant_client import AsyncQdrantClient
from tiktoken import encoding_name_for_model

from review_summary.config.settings import get_settings
from review_summary.query.base import SearchResult
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
        self, neo4j_driver: AsyncDriver, qdrant_client: AsyncQdrantClient
    ) -> None:
        """Initialize the agent executor with required clients.

        Arguments:
            neo4j_driver: Async Neo4j driver for graph database operations
            qdrant_client: Async Qdrant client for vector store operations
        """
        self.neo4j_driver = neo4j_driver
        self.qdrant_client = qdrant_client

        # Cache settings to avoid repeated calls
        self.openai_settings = get_settings().openai

        # Initialize core components (lazy initialization on first use)
        # These are cached across requests for better performance
        self._chat_model: ChatOpenAI | None = None
        self._embedding_model: OpenAIEmbeddings | None = None
        self._tokenizer: TiktokenTokenizer | None = None
        self._search_engine: LocalSearch | None = None

        logger.info("A2aAgentExecutor initialized successfully")

    async def _init_vector_stores(
        self,
    ) -> tuple[EntityVectorStore, TextUnitVectorStore]:
        """Initialize vector stores in parallel for better performance.

        Returns:
            Tuple of (entity_store, text_unit_store)
        """
        logger.debug("Initializing vector stores in parallel")
        entity_store, textunit_store = await asyncio.gather(
            EntityVectorStore.create_vector_store(client=self.qdrant_client),
            TextUnitVectorStore.create_vector_store(client=self.qdrant_client),
        )
        logger.debug("Vector stores initialized successfully")
        return entity_store, textunit_store

    def _get_chat_model(self) -> ChatOpenAI:
        """Get or create the chat model instance (lazy initialization).

        Returns:
            Initialized ChatOpenAI instance
        """
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
        """Get or create the embedding_model instance (lazy initialization).

        Returns:
            Initialized OpenAIEmbeddings instance
        """
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
        """Get or create the tokenizer instance (lazy initialization).

        Returns:
            Initialized TiktokenTokenizer instance
        """
        if self._tokenizer is None:
            chat_model = self._get_chat_model()
            encoding_name = encoding_name_for_model(chat_model.model_name)
            logger.debug(
                f"Initializing TiktokenTokenizer with encoding: {encoding_name}"
            )
            self._tokenizer = TiktokenTokenizer(encoding_name)
        return self._tokenizer

    async def _init_search_engine(self) -> LocalSearch:
        """Initialize or get the cached search instance with all dependencies.

        The search instance is cached after first initialization for better performance.
        This is safe because the underlying components (vector stores, models) maintain
        their own connections and state.

        Returns:
            Initialized LocalSearch instance
        """
        if self._search_engine is None:
            logger.debug("Initializing LocalSearch with all dependencies")

            # Initialize vector stores in parallel
            entity_store, textunit_store = await self._init_vector_stores()

            # Get cached model instances (reused across requests for efficiency)
            chat_model = self._get_chat_model()
            embedding_model = self._get_embedding_model()
            tokenizer = self._get_tokenizer()

            # Build context builder
            context_builder = LocalSearchMixedContext(
                entity_text_embeddings=entity_store,
                text_unit_store=textunit_store,
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

    def _validate_context(self, context: RequestContext) -> tuple[str, str]:
        """Validate and extract required information from request context.

        Arguments:
            context: The request context to validate

        Returns:
            Tuple of (query, target_id)

        Raises:
            KeyError: If target_id is missing from metadata
        """
        query = context.get_user_input()

        # Access metadata["target_id"] directly to maintain KeyError behavior if missing
        target_id = context.metadata["target_id"]

        logger.debug(
            f"Context validated - query length: {len(query)}, target_id: {target_id}"
        )
        return query, target_id

    async def _ensure_task(
        self, context: RequestContext, event_queue: EventQueue
    ) -> Task:
        """Ensure a task exists for the current execution."""
        task = context.current_task
        if not task:
            task = new_task(context.message)  # type: ignore
            await event_queue.enqueue_event(task)
            logger.debug(f"Created new task with id: {task.id}")
        return task

    async def _execute_search(
        self, query: str, target_id: str, updater: TaskUpdater
    ) -> SearchResult:
        """Execute the search operation with progress updates."""
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(
                text="Collecting attraction information...",
                context_id=updater.context_id,
                task_id=updater.task_id,
            ),
        )

        # Initialize search engine
        search = await self._init_search_engine()

        await updater.update_status(
            TaskState.working,
            new_agent_text_message(
                "Searching reviews for attraction...",
                updater.context_id,
                updater.task_id,
            ),
        )

        # Execute search
        logger.info(f"Executing search for target_id: {target_id}")
        result = await search.search(query=query, target_id=target_id)
        logger.info(
            f"Search completed - "
            f"tokens: {result.prompt_tokens + result.output_tokens}, "
            f"time: {result.completion_time:.2f}s"
        )
        return result

    async def _handle_success(self, result: SearchResult, updater: TaskUpdater) -> None:
        """Handle successful search result."""
        metadata: dict[str, Any] = {
            "completion_time": result.completion_time,
            "llm_calls": result.llm_calls,
            "prompt_tokens": result.prompt_tokens,
            "output_tokens": result.output_tokens,
        }

        if isinstance(result.response, str):
            parts = [Part(root=TextPart(text=result.response))]
        elif isinstance(result.response, dict):
            parts = [Part(root=DataPart(data=result.response))]
        else:
            parts = [Part(root=DataPart(data=item)) for item in result.response]

        await updater.add_artifact(parts=parts, metadata=metadata)
        await updater.complete()
        logger.info(f"Task {updater.task_id} completed successfully")

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
            TaskState.failed,
            new_agent_text_message(error_msg, updater.context_id, updater.task_id),
            final=True,
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the review summary agent workflow.

        This method orchestrates the complete process of:
        1. Validating input
        2. Initializing components
        3. Executing search
        4. Returning results
        """
        task = await self._ensure_task(context, event_queue)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            # Validate and extract input
            query, target_id = self._validate_context(context)

            # Execute search with progress updates
            result = await self._execute_search(query, target_id, updater)

            # Handle successful result
            await self._handle_success(result, updater)

        except Exception as e:
            # Handle any errors that occur during execution
            await self._handle_error(e, updater)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the current task execution."""
        task = context.current_task
        if task is None:
            logger.debug("No active task to cancel")
            return

        logger.info(f"Cancelling task {task.id}")
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.update_status(
            TaskState.canceled,
            new_agent_text_message(
                "Review summary request cancelled", task.context_id, task.id
            ),
            final=True,
        )
