import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
from mem0 import AsyncMemory  # type: ignore
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from pymongo import AsyncMongoClient

from chat.config.logging import setup_logging
from chat.config.mem0 import get_mem0_config
from chat.config.settings import get_settings
from chat.infra.nacos.ai import NacosAI
from chat.infra.nacos.naming import NacosNaming
from chat.infra.nacos.utils import client_shutdown
from chat.routers.conversation import conversations
from chat.routers.health import health
from chat.routers.memory import memories
from chat.routers.message import messages

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
    app.include_router(health)
    app.include_router(conversations, prefix="/api/v1")
    app.include_router(memories, prefix="/api/v1")
    app.include_router(messages, prefix="/api/v1")
    return app


app = create_app()
