import logging
import threading
from contextlib import asynccontextmanager
from importlib.metadata import version
from typing import AsyncGenerator

import httpx
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from rocketmq.v5.consumer import (  # type: ignore[import-untyped]
    SimpleConsumer,
)  # pyright: ignore[reportMissingTypeStubs]
from starlette.applications import Starlette

from review_summary.agent.agent import ReviewSummarizerAgent
from review_summary.agent.executor import ReviewSummarizerAgentExecutor
from review_summary.config.settings import get_settings
from review_summary.rocketmq import create_simple_consumer, run_simple_consumer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: Starlette) -> AsyncGenerator[None, None]:
    stop_event = threading.Event()
    consumer: SimpleConsumer | None = None
    consumer_thread: threading.Thread | None = None
    try:
        logger.info("Starting RocketMQ consumer in background...")
        consumer = create_simple_consumer()
        consumer_thread = threading.Thread(
            target=lambda: run_simple_consumer(consumer, stop_event),
            daemon=False,
        )
        consumer_thread.start()
        logger.info("SimpleConsumer background thread started.")
        yield
    except Exception as e:
        logger.error(f"Error during RocketMQ consumer operation: {e}")
    finally:
        stop_event.set()
        logger.info("Shutting down background RocketMQ consumer...")
        if consumer_thread and consumer_thread.is_alive():
            logger.info("Waiting for consumer thread to finish...")
            consumer_thread.join(timeout=20)
            if consumer_thread.is_alive():
                logger.warning("Consumer thread did not exit gracefully!")
            else:
                logger.info("Consumer thread exited successfully.")


def create_a2a_app() -> A2AStarletteApplication:
    """Starts the Review Summarizer Agent server."""

    settings = get_settings()
    capabilities = AgentCapabilities(streaming=True, push_notifications=True)
    skill = AgentSkill(
        id="summarize_reviews",
        name="Review Summarization Tool",
        description="Helps with summarizing reviews of attractions and hotels.",
        tags=["review summarization", "hotel reviews", "attraction reviews"],
        examples=[
            "Summarize the reviews for Eiffel Tower",
            "What do people think about Disneyland?",
            "Can you provide a summary of reviews for this restaurant?",
        ],
    )
    agent_card = AgentCard(
        name="review_summary",
        description="Analyzes customer reviews and provides concise summaries that"
        " answer user questions about hotels and attractions",
        url=f"http://{settings.uvicorn.host}:{settings.uvicorn.port}",
        version=version("review_summary"),
        default_input_modes=ReviewSummarizerAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=ReviewSummarizerAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    httpx_client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(
        httpx_client=httpx_client, config_store=push_config_store
    )
    chat_model = ChatOpenAI(
        model="gpt-4o-2024-08-06",
        temperature=0,
        api_key=settings.openai.api_key,
        base_url=settings.openai.base_url,
    )
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=settings.openai.api_key,
        base_url=settings.openai.base_url,
    )
    request_handler = DefaultRequestHandler(
        agent_executor=ReviewSummarizerAgentExecutor(chat_model, embedding_model),
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender=push_sender,
    )
    server = A2AStarletteApplication(agent_card, request_handler)
    return server


app = create_a2a_app().build(lifespan=lifespan)
