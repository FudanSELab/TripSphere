from typing import Any

from celery import chain
from fastapi import APIRouter
from pydantic import BaseModel, Field

from review_summary.config.query.create_static_summary_config import (
    CreateStaticSummaryConfig,
)
from review_summary.query.tasks.create_static_summary import (
    run_workflow as create_static_summary,
)


class GenerateStaticSummaryRequest(BaseModel):
    target_id: str = Field(
        ..., description="ID of the target to generate the static summary for."
    )
    target_type: str = Field(..., description="Type of the target.")


summaries = APIRouter(prefix="/summaries", tags=["Summaries"])


@summaries.get("")
async def get_static_summary(target_id: str, target_type: str) -> str:
    raise NotImplementedError


@summaries.post("")
async def generate_static_summary(request: GenerateStaticSummaryRequest) -> str:
    pipeline_context: dict[str, Any] = {
        "target_id": request.target_id,
        "target_type": request.target_type,
    }
    create_static_summary_config = CreateStaticSummaryConfig()
    pipeline = chain(
        create_static_summary.s(
            pipeline_context, create_static_summary_config.model_dump()
        ),
    )
    result = pipeline.apply_async()
    return result.id
