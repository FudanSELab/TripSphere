import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from openinference.instrumentation.langchain import LangChainInstrumentor

from itinerary_planner.agent.chat_agent import create_chat_graph
from itinerary_planner.config.logging import setup_logging
from itinerary_planner.config.settings import get_settings
from itinerary_planner.grpc.clients.itinerary import ItineraryServiceClient
from itinerary_planner.nacos.naming import NacosNaming
from itinerary_planner.routers.planning import planning

logger = logging.getLogger(__name__)

setup_logging()
LangChainInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("Starting %s", settings.app.name)
    app.state.ready = False
    app.state.nacos_naming = None

    try:
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
        app.state.ready = True
        yield
    except Exception as e:
        logger.error("Error during lifespan startup: %s", e)
        raise
    finally:
        app.state.ready = False
        nacos_naming = app.state.nacos_naming
        if isinstance(nacos_naming, NacosNaming):
            logger.info("Deregistering service instance...")
            await nacos_naming.deregister(ephemeral=True)
            await nacos_naming.shutdown()


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

    @app.get("/ready", include_in_schema=False)
    async def readiness(  # pyright: ignore[reportUnusedFunction]
        request: Request,
    ) -> dict[str, str]:
        if not getattr(request.app.state, "ready", False):
            raise HTTPException(status_code=503, detail="service is not ready")
        return {"status": "ready"}

    return app


app = create_fastapi_app()
