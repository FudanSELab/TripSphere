import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncGraphDatabase
from openinference.instrumentation.langchain import LangChainInstrumentor
from qdrant_client import AsyncQdrantClient

from review_summary.config.logging import setup_logging
from review_summary.config.settings import get_settings
from review_summary.infra.nacos.naming import NacosNaming
from review_summary.infra.nacos.utils import client_shutdown
from review_summary.mcp import create_review_summary_mcp_server
from review_summary.routers.indices import indices
from review_summary.routers.summaries import summaries
from review_summary.services.summarizer import ReviewSummaryService

logger = logging.getLogger(__name__)

setup_logging()

# Enable OpenInference instrumentation
LangChainInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    app.state.ready = False
    app.state.nacos_naming = None
    app.state.neo4j_driver = AsyncGraphDatabase.driver(  # pyright: ignore
        uri=settings.neo4j.uri,
        auth=(
            settings.neo4j.username,
            settings.neo4j.password.get_secret_value(),
        ),
    )
    app.state.qdrant_client = AsyncQdrantClient(url=settings.qdrant.url)
    try:
        app.state.nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.uvicorn.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        logger.info("Registering service instance...")
        await app.state.nacos_naming.register(ephemeral=True)
        app.state.review_summary_service = ReviewSummaryService(
            neo4j_driver=app.state.neo4j_driver,
            qdrant_client=app.state.qdrant_client,
            nacos_naming=app.state.nacos_naming,
        )
        app.state.ready = True
        async with app.state.review_summary_mcp_app.router.lifespan_context(
            app.state.review_summary_mcp_app
        ):
            yield

    except Exception as e:
        logger.error(f"Error during lifespan startup: {e}")
        raise  # Re-raise to prevent app from starting with errors

    finally:
        app.state.ready = False
        logger.info("Deregistering service instance...")
        if isinstance(app.state.nacos_naming, NacosNaming):
            await app.state.nacos_naming.deregister(ephemeral=True)

        await client_shutdown(app.state.nacos_naming)
        await app.state.qdrant_client.close()
        await app.state.neo4j_driver.close()


def create_fastapi_app() -> FastAPI:
    app_settings = get_settings().app
    app = FastAPI(debug=app_settings.debug, lifespan=lifespan)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,  # ty: ignore[invalid-argument-type]
        allow_origins=["http://localhost:3000"],  # Frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/ready", include_in_schema=False)
    async def readiness(  # pyright: ignore[reportUnusedFunction]
        request: Request,
    ) -> dict[str, str]:
        if not getattr(request.app.state, "ready", False):
            raise HTTPException(status_code=503, detail="service is not ready")
        return {"status": "ready"}

    # Include routers
    app.include_router(indices, prefix="/api/v1")
    app.include_router(summaries, prefix="/api/v1")

    review_summary_mcp = create_review_summary_mcp_server(
        lambda: app.state.review_summary_service
    )
    app.state.review_summary_mcp_app = review_summary_mcp.streamable_http_app()
    app.mount("/", app.state.review_summary_mcp_app)
    return app


app = create_fastapi_app()
