from contextlib import asynccontextmanager
from importlib import metadata
from typing import AsyncGenerator, cast

from litestar import Litestar, get
from pydantic import BaseModel, Field

from chat.config.settings import get_settings
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
        await cast(NacosNaming, nacos_naming).register(True)
        yield
    finally:
        await cast(NacosNaming, nacos_naming).deregister(True)


class RootResponse(BaseModel):
    version: str = Field(
        default_factory=lambda: metadata.version("chat"),
        description="Current version of chat service.",
        examples=["1.0.0", "3.14.0"],
    )


@get("/")
async def root() -> RootResponse:
    """
    Root endpoint for the chat service.
    """
    return RootResponse()


def create_app() -> Litestar:
    application = Litestar([root], lifespan=[nacos])
    return application
