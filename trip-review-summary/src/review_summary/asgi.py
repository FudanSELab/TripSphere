import logging
from contextlib import asynccontextmanager
from importlib.metadata import version
from typing import AsyncGenerator

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
from neo4j import AsyncDriver, AsyncGraphDatabase
from qdrant_client import AsyncQdrantClient

from review_summary.agent.executor import ReviewSummaryAgentExecutor
from review_summary.config.logging import setup_logging
from review_summary.config.settings import get_settings
from review_summary.infra.nacos.naming import NacosNaming
from review_summary.infra.qdrant.bootstrap import bootstrap
from review_summary.routers.indices import indices
from review_summary.routers.summaries import summaries
from review_summary.routers.tasks import tasks

logger = logging.getLogger(__name__)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    app.state.httpx_client = AsyncClient()
    app.state.neo4j_driver = (  # noqa
        AsyncGraphDatabase.driver(  # pyright: ignore[reportUnknownMemberType]
            settings.neo4j.uri,
            auth=(settings.neo4j.username, settings.neo4j.password.get_secret_value()),
        )
    )
    app.state.qdrant_client = AsyncQdrantClient(url=settings.qdrant.url)
    await bootstrap(app.state.qdrant_client)
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
        app.mount(
            "/",
            create_a2a_app(
                httpx_client=app.state.httpx_client,
                neo4j_driver=app.state.neo4j_driver,
                qdrant_client=app.state.qdrant_client,
            ).build(),
        )
        yield

    except Exception as e:
        logger.error(f"Error during lifespan startup: {e}")
        raise  # Re-raise to prevent app from starting with errors

    finally:
        logger.info("Deregistering service instance...")
        if isinstance(app.state.nacos_naming, NacosNaming):
            await app.state.nacos_naming.deregister(ephemeral=True)
        await app.state.qdrant_client.close()
        await app.state.neo4j_driver.close()
        await app.state.httpx_client.aclose()


def create_a2a_app(
    httpx_client: AsyncClient,
    neo4j_driver: AsyncDriver,
    qdrant_client: AsyncQdrantClient,
) -> A2AStarletteApplication:
    """Create the A2A Starlette application."""
    uvicorn_settings = get_settings().uvicorn
    capabilities = AgentCapabilities(streaming=True)
    summarize_reviews = AgentSkill(
        id="summarize_reviews",
        name="Review Summarization",
        description="Helps with summarizing reviews of attractions.",
        tags=["review summary", "attraction reviews"],
        examples=[
            "What do people think about Shanghai Disneyland?",
            "Can you provide a summary of reviews for West Lake?",
        ],
    )
    agent_card = AgentCard(
        name="review_summary",
        description=(
            "Analyze customer reviews and provide concise summaries "
            "that answer user questions about attractions."
        ),
        url=f"http://{uvicorn_settings.host}:{uvicorn_settings.port}",
        version=version("review_summary"),
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=capabilities,
        skills=[summarize_reviews],
    )
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(httpx_client, push_config_store)
    http_handler = DefaultRequestHandler(
        agent_executor=ReviewSummaryAgentExecutor(neo4j_driver, qdrant_client),
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
    app.include_router(tasks, prefix="/api/v1")
    return app


app = create_fastapi_app()
