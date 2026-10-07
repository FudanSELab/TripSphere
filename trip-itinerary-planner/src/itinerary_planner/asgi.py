import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openinference.instrumentation.langchain import LangChainInstrumentor

from itinerary_planner.agent.chat_agent import create_chat_graph
from itinerary_planner.config.logging import setup_logging
from itinerary_planner.config.settings import get_settings
from itinerary_planner.grpc.clients.itinerary import ItineraryServiceClient
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.nacos.prompts import (
    PromptSpec,
    PromptStore,
    clear_active_prompts,
    set_active_prompts,
)
from itinerary_planner.prompts.chat_agent import CHAT_AGENT_INSTRUCTION
from itinerary_planner.prompts.workflow import (
    MARKDOWN_GENERATION_PROMPT,
    REGENERATE_DAY_PROMPT,
    RESEARCH_AND_PLAN_PROMPT,
)
from itinerary_planner.routers.planning import planning

logger = logging.getLogger(__name__)

setup_logging()
LangChainInstrumentor().instrument()

PROMPT_SPECS = (
    PromptSpec(
        key="itinerary-chat",
        data_id="tripsphere.itinerary-planner.chat-prompt",
        default=CHAT_AGENT_INSTRUCTION,
    ),
    PromptSpec(
        key="itinerary-research",
        data_id="tripsphere.itinerary-planner.research-prompt",
        default=RESEARCH_AND_PLAN_PROMPT,
        required_fields=(
            "num_days",
            "destination",
            "interests",
            "pace",
            "activities_per_day",
            "start_date",
            "end_date",
            "additional_preferences",
            "attractions",
        ),
    ),
    PromptSpec(
        key="itinerary-markdown",
        data_id="tripsphere.itinerary-planner.markdown-prompt",
        default=MARKDOWN_GENERATION_PROMPT,
        required_fields=("itinerary_json",),
    ),
    PromptSpec(
        key="itinerary-regenerate-day",
        data_id="tripsphere.itinerary-planner.regenerate-day-prompt",
        default=REGENERATE_DAY_PROMPT,
        required_fields=(
            "day",
            "destination",
            "date",
            "preference",
            "attractions",
        ),
    ),
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    prompt_store: PromptStore | None = None
    app.state.nacos_naming = None
    logger.info(
        "Loaded settings for %s on %s:%s",
        settings.app.name,
        settings.uvicorn.host,
        settings.uvicorn.port,
    )

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
        app.state.nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)

        app.state.itinerary_service_client = ItineraryServiceClient(
            nacos_naming=app.state.nacos_naming
        )

        # CopilotKit AG-UI endpoint
        chat_graph = create_chat_graph(nacos_naming=app.state.nacos_naming)
        chat_agent = LangGraphAgent(name="itinerary_planner", graph=chat_graph)
        add_langgraph_fastapi_endpoint(app, chat_agent, "/")
        yield
    except Exception:
        logger.exception("Error during lifespan startup")
        raise
    finally:
        clear_active_prompts()
        if prompt_store is not None:
            await prompt_store.close()
        if isinstance(app.state.nacos_naming, NacosNaming):
            logger.info("Deregistering service instance...")
            await app.state.nacos_naming.deregister(ephemeral=True)
            await app.state.nacos_naming.shutdown()


def create_fastapi_app() -> FastAPI:
    app_settings = get_settings().app
    app = FastAPI(debug=app_settings.debug, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(planning, prefix="/api/v1")
    return app


app = create_fastapi_app()
