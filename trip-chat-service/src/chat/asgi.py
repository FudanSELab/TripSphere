from contextlib import asynccontextmanager
from importlib import metadata
from typing import AsyncGenerator, cast

from litestar import Litestar, Router, get
from pydantic import BaseModel, Field

from chat.config.settings import get_settings
from chat.controllers import (
    ChatController,
    ConversationController,
    MessageController,
    TaskController,
)
from chat.infra.nacos.naming import NacosNaming


@asynccontextmanager
async def nacos(app: Litestar) -> AsyncGenerator[None, None]:
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


class RootResponse(BaseModel):
    version: str = Field(
        description="Current version of chat service.",
        examples=["3.14.1"],
    )


@get("/")
async def root() -> RootResponse:
    """
    Root endpoint.
    """
    return RootResponse(version=metadata.version("chat"))


def create_app() -> Litestar:
    v1_router = Router(
        path="/api/v1",
        route_handlers=[
            ConversationController,
            MessageController,
            ChatController,
            TaskController,
        ],
    )
    application = Litestar([root, v1_router], lifespan=[nacos])
    return application
