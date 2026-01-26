import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
from neo4j import AsyncDriver, AsyncGraphDatabase
from openinference.instrumentation.langchain import LangChainInstrumentor
from qdrant_client import AsyncQdrantClient

from review_summary.agent.card import agent_card
from review_summary.agent.executor import A2aAgentExecutor
from review_summary.config.logging import setup_logging
from review_summary.config.settings import get_settings
from review_summary.infra.nacos.ai import NacosAI
from review_summary.infra.nacos.naming import NacosNaming
from review_summary.infra.nacos.utils import client_shutdown
from review_summary.routers.indices import indices
from review_summary.routers.summaries import summaries

logger = logging.getLogger(__name__)

setup_logging()

# Enable OpenInference instrumentation
LangChainInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    app.state.httpx_client = AsyncClient()
    app.state.neo4j_driver = AsyncGraphDatabase.driver(  # pyright: ignore
        uri=settings.neo4j.uri,
        auth=(
            settings.neo4j.username,
            settings.neo4j.password.get_secret_value(),
        ),
    )
    app.state.qdrant_client = AsyncQdrantClient(url=settings.qdrant.url)
    try:
        app.state.nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)

        # Defer mounting A2A app until dependencies are ready
        a2a_app = create_a2a_app(
            httpx_client=app.state.httpx_client,
            neo4j_driver=app.state.neo4j_driver,
            qdrant_client=app.state.qdrant_client,
        )
        a2a_app.add_routes_to_app(app)

        app.state.nacos_ai = await NacosAI.create_nacos_ai(
            agent_name=agent_card.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
        )
        # Release A2A AgentCard to Nacos AI Service
        await app.state.nacos_ai.release_agent_card(agent_card)
        logger.info("Registering agent endpoint...")
        await app.state.nacos_ai.register(agent_card.version)
        yield

    except Exception as e:
        logger.error(f"Error during lifespan startup: {e}")
        raise  # Re-raise to prevent app from starting with errors

    finally:
        logger.info("Deregistering agent endpoint...")
        if isinstance(app.state.nacos_ai, NacosAI):
            await app.state.nacos_ai.deregister(agent_card.version)

        logger.info("Deregistering service instance...")
        if isinstance(app.state.nacos_naming, NacosNaming):
            await app.state.nacos_naming.deregister(ephemeral=True)

        await client_shutdown(app.state.nacos_ai, app.state.nacos_naming)
        await app.state.qdrant_client.close()
        await app.state.neo4j_driver.close()
        await app.state.httpx_client.aclose()


def create_a2a_app(
    httpx_client: AsyncClient,
    neo4j_driver: AsyncDriver,
    qdrant_client: AsyncQdrantClient,
) -> A2AStarletteApplication:
    """Create the A2A Starlette application."""
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(httpx_client, push_config_store)
    http_handler = DefaultRequestHandler(
        agent_executor=A2aAgentExecutor(neo4j_driver, qdrant_client),
        task_store=InMemoryTaskStore(),
        push_config_store=push_config_store,
        push_sender=push_sender,
    )
    return A2AStarletteApplication(agent_card, http_handler)


def create_fastapi_app() -> FastAPI:
    app_settings = get_settings().app
    app = FastAPI(debug=app_settings.debug, lifespan=lifespan)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,  # ty: ignore[invalid-argument-type]
        allow_origins=["http://localhost:3000"],  # Frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(indices, prefix="/api/v1")
    app.include_router(summaries, prefix="/api/v1")
    return app


app = create_fastapi_app()
