import logging
from contextlib import asynccontextmanager
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, AsyncGenerator

from httpx import AsyncClient
from litestar import Litestar, Router
from litestar.contrib.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin
from litestar.logging import LoggingConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from pymongo import AsyncMongoClient

from chat.config.settings import get_settings
from chat.controllers import (
    ChatController,
    ConversationController,
    MemoryController,
    MessageController,
    TaskController,
)
from chat.infra.nacos.naming import NacosNaming

logger = logging.getLogger(__name__)


@asynccontextmanager
async def httpx_client(app: Litestar) -> AsyncGenerator[None, None]:
    """
    AsyncClient has built-in connection pooling.
    """
    httpx_client = getattr(app.state, "httpx_client", None)
    if httpx_client is None:
        httpx_client = AsyncClient()
        app.state.httpx_client = httpx_client
    try:
        yield
    finally:
        await httpx_client.aclose()


@asynccontextmanager
async def mongo_client(app: Litestar) -> AsyncGenerator[None, None]:
    """
    AsyncMongoClient has built-in connection pooling.
    """
    mongo_client = getattr(app.state, "mongo_client", None)
    if mongo_client is None:
        settings = get_settings()
        mongo_client = AsyncMongoClient[dict[str, Any]](settings.mongo.uri)
        app.state.mongo_client = mongo_client
    try:
        yield
    finally:
        await mongo_client.close()


@asynccontextmanager
async def nacos_naming(app: Litestar) -> AsyncGenerator[None, None]:
    nacos_naming = getattr(app.state, "nacos_naming", None)
    if nacos_naming is None:
        settings = get_settings()
        nacos_naming = await NacosNaming.create_naming(
            settings.app.name,
            settings.server.port,
            settings.nacos.server_address,
            settings.nacos.namespace_id,
        )
        app.state.nacos_naming = nacos_naming
    try:
        logger.info("Registering service instance...")
        await nacos_naming.register(ephemeral=True)
        yield
    finally:
        logger.info("Deregistering service instance...")
        await nacos_naming.deregister(ephemeral=True)


def configure_logging() -> LoggingConfig:
    settings = get_settings()

    chat_handlers = ["queue_listener"]
    handlers: dict[str, dict[str, Any]] = {}

    if settings.logs.file or settings.logs.level == "DEBUG":
        Path("logs").mkdir(parents=True, exist_ok=True)
        # Compatibility with Windows file naming restrictions
        timestamp = datetime.now().isoformat().replace(":", "-")
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": f"logs/{timestamp}.log",
            "level": "DEBUG",
            "formatter": "standard",
        }
        chat_handlers.append("file")

    logging_config = LoggingConfig(
        configure_root_logger=False,
        handlers=handlers,
        loggers={
            "chat": {
                "level": settings.logs.level,
                "handlers": chat_handlers,
                "propagate": False,
            }
        },
    )

    logging_config.formatters["standard"] = {
        "format": "%(levelname)s - %(asctime)s - %(name)s "
        "- %(filename)s:%(lineno)d - %(message)s"
    }
    return logging_config


def create_app() -> Litestar:
    v1_router = Router(
        path="/api/v1",
        route_handlers=[
            ChatController,
            ConversationController,
            MemoryController,
            MessageController,
            TaskController,
        ],
    )
    openapi_config = OpenAPIConfig(
        title=get_settings().app.name,
        version=version("chat"),
        render_plugins=[ScalarRenderPlugin()],
    )
    opentelemetry_config = OpenTelemetryConfig()
    logging_config = configure_logging()
    application = Litestar(
        [v1_router],
        openapi_config=openapi_config,
        lifespan=[httpx_client, mongo_client, nacos_naming],
        plugins=[OpenTelemetryPlugin(config=opentelemetry_config)],
        logging_config=logging_config,
    )
    return application
