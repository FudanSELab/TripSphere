import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TaskState, TextPart
from a2a.utils import new_agent_text_message, new_task
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from neo4j import AsyncDriver
from qdrant_client import AsyncQdrantClient
from tiktoken import encoding_name_for_model

from review_summary.config.settings import get_settings
from review_summary.query.structured_search.local_search.mixed_content import (
    LocalSearchMixedContext,
)
from review_summary.query.structured_search.local_search.search import LocalSearch
from review_summary.tokenizer.tiktoken import TiktokenTokenizer
from review_summary.vector_stores.entity import EntityVectorStore
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)


class A2aAgentExecutor(AgentExecutor):
    def __init__(
        self, neo4j_driver: AsyncDriver, qdrant_client: AsyncQdrantClient
    ) -> None:
        self.neo4j_driver = neo4j_driver
        self.qdrant_client = qdrant_client

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        openai_settings = get_settings().openai

        query = context.get_user_input()

        target_id = context.metadata["target_id"]

        task = context.current_task
        if not task:
            task = new_task(context.message)  # type: ignore
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    text="Finding attraction information...",
                    context_id=task.context_id,
                    task_id=task.id,
                ),
            )

            entity_store = await EntityVectorStore.create_vector_store(
                client=self.qdrant_client
            )

            textunit_store = await TextUnitVectorStore.create_vector_store(
                client=self.qdrant_client
            )

            chat_model = ChatOpenAI(
                model="gpt-4o",
                temperature=0.0,
                api_key=openai_settings.api_key,
                base_url=openai_settings.base_url,
            )

            embedder = OpenAIEmbeddings(
                model="text-embedding-3-large",
                api_key=openai_settings.api_key,
                base_url=openai_settings.base_url,
            )

            tokenizer = TiktokenTokenizer(
                encoding_name_for_model(chat_model.model_name)
            )

            context_builder = LocalSearchMixedContext(
                entity_text_embeddings=entity_store,
                text_unit_store=textunit_store,
                neo4j_driver=self.neo4j_driver,
                tokenizer=tokenizer,
                text_embedder=embedder,
            )

            search = LocalSearch(
                chat_model=chat_model,
                context_builder=context_builder,
                tokenizer=tokenizer,
            )

            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "Searching reviews for attraction...",
                    task.context_id,
                    task.id,
                ),
            )

            result = await search.search(query=query, target_id=target_id)

            metadata = {
                "completion_time": result.completion_time,
                "llm_calls": result.llm_calls,
                "prompt_tokens": result.prompt_tokens,
                "output_tokens": result.output_tokens,
            }
            await updater.add_artifact(
                [Part(root=TextPart(text=str(result.response)))],
                name="review_summary",
                metadata=metadata,
            )
            await updater.complete()

        except Exception as e:
            error_msg = f"Error processing review summary: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    text=error_msg, context_id=task.context_id, task_id=task.id
                ),
                final=True,
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        if not task:
            return

        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.update_status(
            TaskState.canceled,
            new_agent_text_message(
                "Review summary request cancelled",
                task.context_id,
                task.id,
            ),
            final=True,
        )
