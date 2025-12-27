import logging
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
from qdrant_client import AsyncQdrantClient
from starlette.applications import Starlette

from review_summary.agent.agent import ReviewSummaryAgent
from review_summary.agent.executor import ReviewSummaryAgentExecutor
from review_summary.config.logging import setup_logging
from review_summary.config.settings import get_settings
from review_summary.infra.nacos.naming import NacosNaming
from review_summary.infra.rocketmq.consumer import RocketMQConsumer
from review_summary.vector_stores.qdrant import ReviewVectorStore

logger = logging.getLogger(__name__)

setup_logging()

qdrant_client = AsyncQdrantClient(url=get_settings().qdrant.url)
repository: ReviewVectorStore | None = None
nacos_naming: NacosNaming | None = None


@asynccontextmanager
async def lifespan(_: Starlette) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    consumer: RocketMQConsumer | None = None
    global qdrant_client, repository, nacos_naming
    try:
        repository = await ReviewVectorStore.create_repository(qdrant_client)
        logger.info("Starting up RocketMQConsumer...")
        consumer = RocketMQConsumer()
        nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await nacos_naming.register(ephemeral=True)
        yield

    except Exception as e:
        logger.error(f"Error during lifespan startup: {e}", exc_info=True)
        raise  # Re-raise to prevent app from starting with failed consumer

    finally:
        logger.info("Deregistering service instance...")
        if isinstance(nacos_naming, NacosNaming):
            await nacos_naming.deregister(ephemeral=True)
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
            "What do people think about Shanghai Disneyland?",
            "Can you provide a summary of reviews for the Bund in Shanghai?",
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
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=capabilities,
        skills=[agent_skill],
    )
    httpx_client = httpx.AsyncClient()
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(httpx_client, push_config_store)
    agent = ReviewSummaryAgent()
    http_handler = DefaultRequestHandler(
        agent_executor=ReviewSummaryAgentExecutor(agent),
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender=push_sender,
    )
    a2a_app = A2AStarletteApplication(agent_card, http_handler)
    return a2a_app


app = create_a2a_app().build(lifespan=lifespan)
