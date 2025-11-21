from contextlib import asynccontextmanager
from importlib.metadata import version
from typing import Any, AsyncGenerator, cast

from litestar import Litestar, Router
from litestar.contrib.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from pymongo import AsyncMongoClient

from chat.config.settings import get_settings
from chat.controllers import (
    ChatController,
    ConversationController,
    MessageController,
    TaskController,
)
from chat.infra.nacos.naming import NacosNaming


@asynccontextmanager
async def mongo_client(app: Litestar) -> AsyncGenerator[None, None]:
    """
    PyMongo uses built-in connection pool. Only one client is required.
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
        await cast(NacosNaming, nacos_naming).register(ephemeral=True)
        yield
    finally:
        await cast(NacosNaming, nacos_naming).deregister(ephemeral=True)


def create_app() -> Litestar:
    v1_router = Router(
        path="/api/v1",
        route_handlers=[
            MessageController,
            ConversationController,
            ChatController,
            TaskController,
        ],
    )
    openapi_config = OpenAPIConfig(
        title=get_settings().app.name,
        version=version("chat"),
        render_plugins=[ScalarRenderPlugin()],
    )
    opentelemetry_config = OpenTelemetryConfig()
    application = Litestar(
        [v1_router],
        openapi_config=openapi_config,
        lifespan=[mongo_client, nacos_naming],
        plugins=[OpenTelemetryPlugin(config=opentelemetry_config)],
    )
    return application
