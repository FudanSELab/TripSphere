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

from itinerary_planner.agent.card import agent_card
from itinerary_planner.agent.executor import A2aAgentExecutor
from itinerary_planner.config.logging import setup_logging
from itinerary_planner.config.settings import get_settings
from itinerary_planner.nacos.ai import NacosAI
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.nacos.utils import client_shutdown
from itinerary_planner.routers.itineraries import itineraries

logger = logging.getLogger(__name__)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    # Initialize HTTP client
    app.state.httpx_client = AsyncClient()

    try:
        # Register with Nacos
        app.state.nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)

        # Create and mount A2A application
        a2a_app = create_a2a_app(httpx_client=app.state.httpx_client)
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
        await app.state.httpx_client.aclose()


def create_a2a_app(httpx_client: AsyncClient) -> A2AStarletteApplication:
    """Create the A2A Starlette application."""
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(httpx_client, push_config_store)
    http_handler = DefaultRequestHandler(
        agent_executor=A2aAgentExecutor(),
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
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(itineraries)
    return app


app = create_fastapi_app()
