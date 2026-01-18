import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from starlette.applications import Starlette

from journey_assistant.agent import agent_card, get_root_agent
from journey_assistant.config.settings import get_settings
from journey_assistant.nacos.ai import NacosAI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    try:
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
        raise

    finally:
        logger.info("Deregistering agent endpoint...")
        if isinstance(app.state.nacos_ai, NacosAI):
            await app.state.nacos_ai.deregister(agent_card.version)
            await app.state.nacos_ai.shutdown()


def create_app() -> Starlette:
    app = Starlette(lifespan=lifespan)
    app.mount("/", to_a2a(get_root_agent(), agent_card=agent_card))
    return app


app = create_app()
