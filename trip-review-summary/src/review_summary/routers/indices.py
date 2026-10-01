from typing import Any, Literal

from celery import chain
from fastapi import APIRouter
from pydantic import BaseModel, Field

from review_summary.config.index.create_text_embeddings_config import (
    CreateTextEmbeddingsConfig,
)
from review_summary.config.index.extract_graph_config import ExtractGraphConfig
from review_summary.config.index.finalize_graph_config import FinalizeGraphConfig
from review_summary.correlation import ensure_request_id
from review_summary.index.tasks.collect_text_units import (
    run_workflow as collect_text_units,
)
from review_summary.index.tasks.create_communities import (
    run_workflow as create_communities,
)
from review_summary.index.tasks.create_community_reports import (
    run_workflow as create_community_reports,
)
from review_summary.index.tasks.create_final_text_units import (
    run_workflow as create_final_text_units,
)
from review_summary.index.tasks.create_text_embeddings import (
    run_workflow as create_text_embeddings,
)
from review_summary.index.tasks.extract_graph import run_workflow as extract_graph
from review_summary.index.tasks.finalize_graph import run_workflow as finalize_graph


class BuildIndexRequest(BaseModel):
    target_id: str = Field(
        ..., description="ID of the target to build the graph index for."
    )
    target_type: Literal["attraction", "hotel"] = Field(
        default="attraction", description="Type of the target."
    )


class TaskSubmitResponse(BaseModel):
    task_id: str = Field(..., description="ID of the graph indexing (Celery) Task.")


indices = APIRouter(prefix="/indices", tags=["Indices"])


@indices.post("")
async def build_graph_index(request: BuildIndexRequest) -> TaskSubmitResponse:
    request_id = ensure_request_id()
    pipeline_context: dict[str, Any] = {
        "target_id": request.target_id,
        "target_type": request.target_type,
        "vector_dim": 3072,  # Vector dimension of embeddings
        "request_id": request_id,
    }
    extract_graph_config = ExtractGraphConfig(
        # For extract_graph operation
        graph_llm_config={"model": "gpt-4o", "temperature": 0.3},
        # For summarize_descriptions operation
        summary_llm_config={"model": "gpt-4o", "temperature": 0.3},
    )
    finalize_graph_config = FinalizeGraphConfig()
    create_text_embeddings_config = CreateTextEmbeddingsConfig(
        embedding_llm_config={"model": "text-embedding-3-large"}
    )
    task_headers = {"request_id": request_id}
    pipeline = chain(
        collect_text_units.s(pipeline_context).set(headers=task_headers),
        extract_graph.s(extract_graph_config.model_dump()).set(
            headers=task_headers
        ),
        finalize_graph.s(finalize_graph_config.model_dump()).set(
            headers=task_headers
        ),
        create_communities.s().set(headers=task_headers),
        create_final_text_units.s().set(headers=task_headers),
        create_community_reports.s().set(headers=task_headers),
        create_text_embeddings.s(
            create_text_embeddings_config.model_dump()
        ).set(headers=task_headers),
    )
    result = pipeline.apply_async(headers={"request_id": request_id})
    return TaskSubmitResponse(task_id=result.id)


@indices.delete("/{target_id}")
async def delete_graph_index(target_id: str) -> None:
    raise NotImplementedError
