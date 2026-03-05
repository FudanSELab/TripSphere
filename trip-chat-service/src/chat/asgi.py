import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint  # type: ignore
from ag_ui_adk.endpoint import make_extract_headers  # type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
from mem0 import AsyncMemory  # type: ignore
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from pymongo import AsyncMongoClient

from chat.agent.facade import AgentFacadeFactory
from chat.agent.memory import Mem0MemoryService
from chat.agent.session import MongoSessionService
from chat.config.logging import setup_logging
from chat.config.mem0 import get_mem0_config
from chat.config.settings import get_settings
from chat.nacos.ai import NacosAI
from chat.nacos.naming import NacosNaming
from chat.nacos.utils import client_shutdown
from chat.routers.health import health

logger = logging.getLogger(__name__)

setup_logging()

# Enable OpenInference instrumentation
LiteLLMInstrumentor().instrument()
GoogleADKInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    app.state.httpx_client = AsyncClient()
    app.state.mongo_client = AsyncMongoClient[dict[str, Any]](settings.mongo.uri)
    try:
        app.state.memory_engine = await AsyncMemory.from_config(get_mem0_config())
        app.state.nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)
        app.state.nacos_ai = await NacosAI.create_nacos_ai(
            server_address=settings.nacos.server_address
        )

        # Add the ADK endpoint
        agent_facade_factory = AgentFacadeFactory(
            httpx_client=app.state.httpx_client, nacos_ai=app.state.nacos_ai
        )
        agent_facade = await agent_facade_factory.create_facade()
        memory_service = Mem0MemoryService(app.state.memory_engine)
        session_service = MongoSessionService(app.state.mongo_client)
        root_agent = ADKAgent(
            adk_agent=agent_facade,
            app_name=settings.app.name,
            user_id_extractor=lambda input: input.state.get("headers", {}).get(
                "user_id", "anonymous"
            ),
            memory_service=memory_service,
            session_service=session_service,
        )
        add_adk_fastapi_endpoint(
            app,
            root_agent,
            extract_state_from_request=make_extract_headers(["x-user-id"]),
        )
        yield
    except Exception as e:
        logger.error(f"Exception during lifespan startup: {e}")
        raise
    finally:
        logger.info("Deregistering service instance...")
        if isinstance(app.state.nacos_naming, NacosNaming):
            await app.state.nacos_naming.deregister(ephemeral=True)
        await client_shutdown(app.state.nacos_ai, app.state.nacos_naming)
        await app.state.mongo_client.close()
        await app.state.httpx_client.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(debug=settings.app.debug, lifespan=lifespan)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,  # ty: ignore[invalid-argument-type]
        allow_origins=["http://localhost:3000"],  # Frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health, prefix="/api/v1")
    return app


app = create_app()
