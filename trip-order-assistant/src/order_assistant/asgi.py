import logging
import warnings
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from a2a.types import AgentCard
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor

from order_assistant.agent import AGENT_NAME, load_agent_card
from order_assistant.config.settings import get_settings
from order_assistant.nacos.ai import NacosAI
from order_assistant.nacos.utils import client_shutdown

# Suppress ADK Experimental Warnings
warnings.filterwarnings("ignore", module=".*")

logger = logging.getLogger(__name__)

# Enable OpenInference instrumentation
LiteLLMInstrumentor().instrument()
GoogleADKInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    agent_card: AgentCard | None = None
    try:
        app.state.nacos_ai = await NacosAI.create_nacos_ai(
            agent_name=AGENT_NAME,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
        )
        agent_card = load_agent_card()
        # Release A2A AgentCard to Nacos AI Service
        await app.state.nacos_ai.release_agent_card(agent_card)
        logger.info("Registering agent endpoint...")
        await app.state.nacos_ai.register(agent_card.version)
        yield
    except Exception as e:
        logger.error(f"Exception during lifespan startup: {e}")
        raise
    finally:
        logger.info("Deregistering agent endpoint...")
        if isinstance(app.state.nacos_ai, NacosAI) and agent_card:
            await app.state.nacos_ai.deregister(agent_card.version)
        from order_assistant.nacos.naming import _nacos_naming  # pyright: ignore

        await client_shutdown(app.state.nacos_ai, _nacos_naming)


def create_app() -> FastAPI:
    settings = get_settings()
    app = get_fast_api_app(
        agents_dir="src/",
        web=True,
        a2a=True,
        host=settings.uvicorn.host,
        port=settings.uvicorn.port,
        lifespan=lifespan,
    )
    return app


app = create_app()
