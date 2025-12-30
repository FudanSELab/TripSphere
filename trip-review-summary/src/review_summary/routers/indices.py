from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from review_summary.common.deps import provide_text_unit_vector_store
from review_summary.vector_stores.text_unit import TextUnitVectorStore


class BuildIndexRequest(BaseModel):
    target_id: str = Field(
        ..., description="ID of the target to build the graph index for."
    )
    target_type: str = Field(default="attraction", description="Type of the target.")


class TaskSubmitResponse(BaseModel):
    task_id: str = Field(..., description="ID of the graph index building task.")


indices = APIRouter(prefix="/indices", tags=["Indices"])


@indices.post("")
async def build_graph_index(
    text_unit_vector_store: Annotated[
        TextUnitVectorStore, Depends(provide_text_unit_vector_store)
    ],
    request: BuildIndexRequest,
) -> TaskSubmitResponse:
    raise NotImplementedError


@indices.delete("")
async def delete_graph_index(attraction_id: str) -> None:
    raise NotImplementedError
