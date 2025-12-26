import logging
from contextlib import asynccontextmanager
from importlib.metadata import version
from typing import AsyncGenerator, cast

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
from qdrant_client import AsyncQdrantClient
from starlette.applications import Starlette

from review_summary.agent.agent import ReviewSummaryAgent
from review_summary.agent.executor import ReviewSummaryAgentExecutor
from review_summary.config.logging import setup_logging
from review_summary.config.settings import get_settings
from review_summary.index.repository import ReviewEmbeddingRepository
from review_summary.infra.nacos.naming import NacosNaming
from review_summary.infra.rocketmq.consumer import RocketMQConsumer

logger = logging.getLogger(__name__)

setup_logging()

qdrant_client = AsyncQdrantClient(url=get_settings().qdrant.url)
repository: ReviewEmbeddingRepository | None = None
nacos_naming: NacosNaming | None = None


@asynccontextmanager
async def lifespan(_: Starlette) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    consumer: RocketMQConsumer | None = None
    global qdrant_client, repository, nacos_naming
    try:
        repository = await ReviewEmbeddingRepository.create_repository(qdrant_client)
        logger.info("Starting up RocketMQConsumer...")
        consumer = RocketMQConsumer(repository)
        nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)
        yield

    except Exception as e:
        logger.error(f"Error during lifespan startup: {e}", exc_info=True)
        raise  # Re-raise to prevent app from starting with failed consumer

    finally:
        logger.info("Deregistering service instance...")
        if isinstance(app.state.nacos_naming, NacosNaming):
            await app.state.nacos_naming.deregister(ephemeral=True)
        logger.info("Shutting down RocketMQConsumer...")
        if isinstance(consumer, RocketMQConsumer):
            await consumer.shutdown()
        await qdrant_client.close()


def create_a2a_app() -> A2AStarletteApplication:
    settings = get_settings()
    capabilities = AgentCapabilities(streaming=True, push_notifications=True)
    agent_skill = AgentSkill(
        id="summarize_reviews",
        name="Review Summary Tool",
        description="Helps with summarizing reviews of attractions and hotels.",
        tags=["review summary", "hotel reviews", "attraction reviews"],
        examples=[
            "Summarize the reviews for Eiffel Tower",
            "What do people think about Disneyland?",
            "Can you provide a summary of reviews for this restaurant?",
        ],
    )
    agent_card = AgentCard(
        name="review_summary",
        description=(
            "Analyzes customer reviews and provides concise summaries that"
            " answer user questions about hotels and attractions"
        ),
        url=f"http://{settings.uvicorn.host}:{settings.uvicorn.port}",
        version=version("review_summary"),
        default_input_modes=ReviewSummaryAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=ReviewSummaryAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[agent_skill],
    )
    httpx_client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(httpx_client, push_config_store)
    chat_model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.openai.api_key,
        base_url=settings.openai.base_url,
    )
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=settings.openai.api_key,
        base_url=settings.openai.base_url,
    )
    global repository
    _repository = cast(ReviewEmbeddingRepository, repository)
    agent = ReviewSummaryAgent(chat_model, embedding_model, _repository)
    http_handler = DefaultRequestHandler(
        agent_executor=ReviewSummaryAgentExecutor(agent),
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender=push_sender,
    )
    a2a_app = A2AStarletteApplication(agent_card, http_handler)
    return a2a_app


app = create_a2a_app().build(lifespan=lifespan)
