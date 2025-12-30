from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from review_summary.utils.sse import encode


class TaskStatus(BaseModel):
    task_id: str = Field(..., description="ID of the task.")


tasks = APIRouter(prefix="/tasks", tags=["Tasks"])


async def _stream_events() -> AsyncGenerator[str, None]:
    yield encode("Placeholder")


@tasks.get("/{task_id}")
async def get_task_status(task_id: str) -> TaskStatus:
    """Get the status of a specific task."""
    raise NotImplementedError


@tasks.post("/{task_id}:subscribe")
async def subscribe_indexing(task_id: str) -> StreamingResponse:
    """Subscribe to the graph indexing process via SSE."""
    return StreamingResponse(_stream_events(), media_type="text/event-stream")
