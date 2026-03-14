import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint  # type: ignore[import-untyped]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from openinference.instrumentation.langchain import LangChainInstrumentor

from itinerary_planner.agent.chat_agent import create_chat_graph
from itinerary_planner.config.logging import setup_logging
from itinerary_planner.config.settings import get_settings
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.routers.planning import planning
from itinerary_planner.storage.itinerary_repo import ItineraryRepo

logger = logging.getLogger(__name__)

setup_logging()
LangChainInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("Loaded settings: %s", settings)

    app.state.httpx_client = AsyncClient()

    # MongoDB / Motor
    mongo_client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb.uri)  # type: ignore[type-arg]
    db = mongo_client[settings.mongodb.database]
    repo = ItineraryRepo(db)
    await repo.ensure_indexes()
    app.state.itinerary_repo = repo
    app.state.mongo_client = mongo_client
    logger.info(
        "MongoDB connected: %s / %s", settings.mongodb.uri, settings.mongodb.database
    )

    try:
        app.state.nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)

        # CopilotKit AG-UI endpoint — served by ag_ui_langgraph
        chat_graph = create_chat_graph(nacos_naming=app.state.nacos_naming)
        chat_agent = LangGraphAgent(
            name="itinerary_planner",
            graph=chat_graph,
            description="AI assistant for modifying and optimizing travel itineraries",
        )
        add_langgraph_fastapi_endpoint(app, chat_agent, "/copilotkit")
        logger.info("AG-UI chat agent endpoint mounted at /copilotkit")

        yield

    except Exception as e:
        logger.error("Error during lifespan startup: %s", e)
        raise

    finally:
        if hasattr(app.state, "nacos_naming") and isinstance(
            app.state.nacos_naming, NacosNaming
        ):
            logger.info("Deregistering service instance...")
            await app.state.nacos_naming.deregister(ephemeral=True)
            await app.state.nacos_naming.shutdown()

        mongo_client.close()
        logger.info("MongoDB connection closed")

        await app.state.httpx_client.aclose()


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
