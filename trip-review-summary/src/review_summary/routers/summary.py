from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from review_summary.utils.sse import encode

reviews_summary = APIRouter(prefix="/reviews/summary", tags=["Review Summary"])


@reviews_summary.get("")
async def get_static_summary(attraction_id: str) -> str:
    raise NotImplementedError


async def _stream_events() -> AsyncGenerator[str, None]:
    yield encode("Placeholder")


@reviews_summary.post(":index")
async def build_graph_index(attraction_id: str) -> StreamingResponse:
    return StreamingResponse(_stream_events(), media_type="text/event-stream")


@reviews_summary.delete(":index")
async def delete_graph_index(attraction_id: str) -> None:
    raise NotImplementedError
