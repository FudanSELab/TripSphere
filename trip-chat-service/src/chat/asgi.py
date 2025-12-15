import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from httpx import AsyncClient
from pymongo import AsyncMongoClient

from chat.config.logging import setup_logging
from chat.config.settings import get_settings
from chat.infra.nacos.naming import NacosNaming
from chat.routers.conversation import conversations
from chat.routers.memory import memories
from chat.routers.message import messages

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    app.state.httpx_client = AsyncClient()
    app.state.mongo_client = AsyncMongoClient[dict[str, Any]](settings.mongo.uri)
    try:
        app.state.nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)
        yield
    except Exception as e:
        logger.error(f"Exception during lifespan startup: {e}")
        raise
    finally:
        logger.info("Deregistering service instance...")
        await app.state.nacos_naming.deregister(ephemeral=True)
        await app.state.mongo_client.close()
        await app.state.httpx_client.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(debug=settings.app.debug, lifespan=lifespan)
    app.include_router(conversations, prefix="/api/v1")
    app.include_router(memories, prefix="/api/v1")
    app.include_router(messages, prefix="/api/v1")
    return app


app = create_app()
