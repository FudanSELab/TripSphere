import json
import logging
import warnings
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint  # type: ignore
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from openinference.instrumentation.langchain import LangChainInstrumentor
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from itinerary_planner.agent.card import agent_card
from itinerary_planner.agent.deep_agent import create_deep_agent
from itinerary_planner.agent.executor import A2aAgentExecutor
from itinerary_planner.config.logging import setup_logging
from itinerary_planner.config.settings import get_settings
from itinerary_planner.nacos.ai import NacosAI
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.nacos.utils import client_shutdown
from itinerary_planner.routers.planning import planning
from itinerary_planner.storage.itinerary_repo import ItineraryRepo

warnings.filterwarnings("ignore", module="google.adk")

logger = logging.getLogger(__name__)

setup_logging()

LangChainInstrumentor().instrument()

_SEP = "═" * 60


class CopilotKitRequestLogger(BaseHTTPMiddleware):
    """Log AG-UI request structure arriving at /copilotkit.

    This lets us verify that useCopilotReadable context (the itinerary)
    is actually being sent from the frontend to the backend agent.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):  # type: ignore
        if request.url.path == "/copilotkit" and request.method == "POST":
            try:
                body_bytes = await request.body()
                body = json.loads(body_bytes)

                logger.info(_SEP)
                logger.info("[CopilotKit] ► Incoming AG-UI request to /copilotkit")

                # Log messages summary
                messages = body.get("messages", [])
                logger.info("[CopilotKit]   messages count: %d", len(messages))
                for i, msg in enumerate(messages[-4:]):  # last 4 messages
                    role = msg.get("role", "?")
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        preview = content[:200].replace("\n", " ↵ ")
                    elif isinstance(content, list):
                        # Array of content parts
                        preview = str(content)[:200]
                    else:
                        preview = str(content)[:200]
                    logger.info(
                        "[CopilotKit]   msg[%d] role=%-12s | %s",
                        len(messages) - 4 + i,
                        role,
                        preview,
                    )

                # Log state/context (this is where useCopilotReadable values appear)
                state = body.get("state", {})
                context = body.get("context", {})
                frontend_actions = body.get("frontend_actions", [])

                if state:
                    state_keys = list(state.keys()) if isinstance(state, dict) else []
                    logger.info("[CopilotKit]   state keys (%d): %s", len(state_keys), state_keys[:10])
                    for sk in state_keys[:5]:
                        sv = state[sk]
                        sv_preview = str(sv)[:200].replace("\n", " ↵ ")
                        logger.info("[CopilotKit]   state[%r] = %s", sk, sv_preview)
                if context:
                    logger.info(
                        "[CopilotKit]   context keys: %s",
                        list(context.keys()) if isinstance(context, dict) else type(context).__name__,
                    )
                if frontend_actions:
                    logger.info(
                        "[CopilotKit]   frontend_actions: %s",
                        [a.get("name", "?") for a in frontend_actions if isinstance(a, dict)],
                    )

                # Log top-level keys for discovery
                logger.info(
                    "[CopilotKit]   top-level keys: %s", list(body.keys())
                )
                logger.info(_SEP)

                # Rebuild request with body (Starlette requires this)
                from starlette.datastructures import Headers
                from starlette.requests import Request as StarletteRequest
                import io

                async def receive():
                    return {"type": "http.request", "body": body_bytes}

                request = Request(request.scope, receive)

            except Exception as exc:
                logger.warning(
                    "[CopilotKit]   Failed to log request body: %s", exc
                )

        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    app.state.httpx_client = AsyncClient()

    # MongoDB / Motor
    mongo_client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb.uri)  # type: ignore[type-arg]
    db = mongo_client[settings.mongodb.database]
    repo = ItineraryRepo(db)
    await repo.ensure_indexes()
    app.state.itinerary_repo = repo
    app.state.mongo_client = mongo_client
    logger.info(
        "MongoDB connected: %s / %s", settings.mongodb.uri, settings.mongodb.database
    )

    try:
        app.state.nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)

        # A2A application
        a2a_app = create_a2a_app(httpx_client=app.state.httpx_client)
        a2a_app.add_routes_to_app(app)

        app.state.nacos_ai = await NacosAI.create_nacos_ai(
            agent_name=agent_card.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
        )
        await app.state.nacos_ai.release_agent_card(agent_card)
        logger.info("Registering agent endpoint...")
        await app.state.nacos_ai.register(agent_card.version)

        # AG-UI endpoint for CopilotKit Deep Agent (pass repo for itinerary injection)
        deep_agent = create_deep_agent(repo=repo)
        adk_agent = ADKAgent(
            adk_agent=deep_agent,
            app_name=settings.app.name,
        )
        add_adk_fastapi_endpoint(app, adk_agent, path="/copilotkit")
        logger.info("AG-UI Deep Agent endpoint mounted at /copilotkit")

        yield

    except Exception as e:
        logger.error(f"Error during lifespan startup: {e}")
        raise

    finally:
        if hasattr(app.state, "nacos_ai") and isinstance(
            app.state.nacos_ai, NacosAI
        ):
            logger.info("Deregistering agent endpoint...")
            await app.state.nacos_ai.deregister(agent_card.version)

        if hasattr(app.state, "nacos_naming") and isinstance(
            app.state.nacos_naming, NacosNaming
        ):
            logger.info("Deregistering service instance...")
            await app.state.nacos_naming.deregister(ephemeral=True)

        nacos_ai = getattr(app.state, "nacos_ai", None)
        nacos_naming = getattr(app.state, "nacos_naming", None)
        if nacos_ai or nacos_naming:
            await client_shutdown(nacos_ai, nacos_naming)

        mongo_client.close()
        logger.info("MongoDB connection closed")

        await app.state.httpx_client.aclose()


def create_a2a_app(httpx_client: AsyncClient) -> A2AStarletteApplication:
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Must be added AFTER CORSMiddleware (Starlette applies middleware in reverse order)
    app.add_middleware(CopilotKitRequestLogger)

    app.include_router(planning, prefix="/api/v1")
    return app




app = create_fastapi_app()
