import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, cast

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint  # type: ignore
from ag_ui_adk.adk_agent import RunAgentInput  # type: ignore
from ag_ui_adk.endpoint import make_extract_headers  # type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mem0 import AsyncMemory  # type: ignore
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from pymongo import AsyncMongoClient

from chat.agent import create_adk_app, create_agent
from chat.agent.memory import Mem0MemoryService
from chat.agent.remote_agent import RemoteAgentsFactory
from chat.agent.session import MongoSessionService
from chat.config.logging import setup_logging
from chat.config.mem0 import get_mem0_config
from chat.config.settings import Settings, get_settings
from chat.nacos.ai import NacosAI
from chat.nacos.naming import NacosNaming
from chat.nacos.utils import client_shutdown
from chat.routers.health import health

logger = logging.getLogger(__name__)

setup_logging()

# Enable OpenInference instrumentation
LiteLLMInstrumentor().instrument()
GoogleADKInstrumentor().instrument()


async def _init_infra(app: FastAPI, settings: Settings) -> None:
    app.state.mongo_client = AsyncMongoClient[Any](settings.mongo.uri)
    app.state.memory_engine = AsyncMemory.from_config(get_mem0_config())
    app.state.nacos_naming = await NacosNaming.create_naming(
        service_name=settings.app.name,
        port=settings.uvicorn.port,
        server_address=settings.nacos.server_address,
        namespace_id=settings.nacos.namespace_id,
    )
    app.state.nacos_ai = await NacosAI.create_nacos_ai(
        server_address=settings.nacos.server_address
    )


async def _init_adk_app(app: FastAPI) -> None:
    remote_agents_factory = RemoteAgentsFactory(app.state.nacos_ai)
    remote_agents = await remote_agents_factory.get_remote_agents()
    root_agent = create_agent(True, sub_agents=remote_agents)  # type: ignore
    adk_app = create_adk_app(root_agent)

    def user_id_extractor(input: RunAgentInput) -> str:
        user_id = input.state.get("headers", {}).get("user_id", "anonymous")
        return cast(str, user_id)

    memory_service = Mem0MemoryService(app.state.memory_engine)
    session_service = MongoSessionService(app.state.mongo_client)
    root_agent = ADKAgent.from_app(
        app=adk_app,
        user_id_extractor=user_id_extractor,
        memory_service=memory_service,
        session_service=session_service,
    )
    add_adk_fastapi_endpoint(
        app=app,
        agent=root_agent,
        extract_state_from_request=make_extract_headers(
            ["x-user-id", "x-user-roles", "authorization"]
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    try:
        await _init_infra(app, settings)
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)
        await _init_adk_app(app)
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
