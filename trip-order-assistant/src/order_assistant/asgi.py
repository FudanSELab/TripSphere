import asyncio
import logging
import warnings
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Iterator, cast

from a2a.server.context import ServerCallContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import ResultAggregator, TaskManager
from a2a.types import AgentCard, MessageSendParams
from google.adk.a2a.utils import agent_to_a2a
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from opentelemetry import context as otel_context
from starlette.applications import Starlette

from order_assistant.agent import (
    AGENT_NAME,
    INSTRUCTION,
    create_agent,
    load_agent_card,
)
from order_assistant.config.logging import setup_logging
from order_assistant.config.settings import get_settings
from order_assistant.nacos.ai import NacosAI
from order_assistant.nacos.prompts import (
    PromptSpec,
    PromptStore,
    clear_active_prompts,
    set_active_prompts,
)
from order_assistant.nacos.utils import client_shutdown

# Suppress ADK Experimental Warnings
warnings.filterwarnings("ignore", module=".*")

logger = logging.getLogger(__name__)
setup_logging()

PROMPT_SPECS = (
    PromptSpec(
        key="order-system",
        data_id="tripsphere.order-assistant.system-prompt",
        default=INSTRUCTION,
        required_fields=("current_datetime",),
    ),
)

# Enable OpenInference instrumentation
LiteLLMInstrumentor().instrument()
GoogleADKInstrumentor().instrument()


class RootedRequestHandler(DefaultRequestHandler):
    async def _setup_message_execution(
        self,
        params: MessageSendParams,
        context: ServerCallContext | None = None,
    ) -> tuple[TaskManager, str, EventQueue, ResultAggregator, asyncio.Task[Any]]:
        trace_token = otel_context.attach(otel_context.Context())
        try:
            return await super()._setup_message_execution(params, context)
        finally:
            otel_context.detach(trace_token)


@contextmanager
def _rooted_a2a_handler() -> Iterator[None]:
    original_handler = agent_to_a2a.DefaultRequestHandler
    agent_to_a2a.DefaultRequestHandler = RootedRequestHandler
    try:
        yield
    finally:
        agent_to_a2a.DefaultRequestHandler = original_handler


def _build_a2a_app(*args: Any, **kwargs: Any) -> Starlette:
    with _rooted_a2a_handler():
        return agent_to_a2a.to_a2a(*args, **kwargs)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncGenerator[None, None]:
    settings = get_settings()
    prompt_store: PromptStore | None = None
    app.state.nacos_ai = None
    logger.info(
        "Loaded settings for %s on %s:%s",
        settings.app.name,
        settings.uvicorn.host,
        settings.uvicorn.port,
    )

    agent_card: AgentCard | None = None
    try:
        prompt_store = await PromptStore.create(
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
            username=settings.nacos.username,
            password=settings.nacos.password.get_secret_value(),
            group=settings.prompt.config_group,
            enabled=settings.prompt.config_enabled,
            required=settings.prompt.config_required,
            timeout_ms=settings.prompt.config_timeout_ms,
        )
        set_active_prompts(await prompt_store.load_all(PROMPT_SPECS))
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
    except Exception:
        logger.exception("Exception during lifespan startup")
        raise
    finally:
        clear_active_prompts()
        if prompt_store is not None:
            await prompt_store.close()
        logger.info("Deregistering agent endpoint...")
        if isinstance(app.state.nacos_ai, NacosAI) and agent_card:
            await app.state.nacos_ai.deregister(agent_card.version)
        from order_assistant.nacos.naming import _nacos_naming  # pyright: ignore

        await client_shutdown(app.state.nacos_ai, _nacos_naming)


def create_app() -> Starlette:
    settings = get_settings()
    root_agent = create_agent()
    agent_card = load_agent_card()
    app = cast(
        Starlette,
        _build_a2a_app(
            root_agent,
            host=settings.uvicorn.host,
            port=settings.uvicorn.port,
            agent_card=agent_card,
            lifespan=lifespan,
        ),
    )
    app.debug = settings.app.debug
    return app


app = create_app()
