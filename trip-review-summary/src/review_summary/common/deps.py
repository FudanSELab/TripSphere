from typing import Annotated, cast

from fastapi import Depends, Request
from neo4j import AsyncDriver
from qdrant_client import AsyncQdrantClient

from review_summary.vector_stores.text_unit import TextUnitVectorStore


def provide_qdrant_client(request: Request) -> AsyncQdrantClient:
    return cast(AsyncQdrantClient, request.app.state.qdrant_client)


def provide_neo4j_driver(request: Request) -> AsyncDriver:
    return cast(AsyncDriver, request.app.state.neo4j_driver)


async def provide_text_unit_vector_store(
    qdrant_client: Annotated[AsyncQdrantClient, Depends(provide_qdrant_client)],
) -> TextUnitVectorStore:
    return TextUnitVectorStore(qdrant_client)
