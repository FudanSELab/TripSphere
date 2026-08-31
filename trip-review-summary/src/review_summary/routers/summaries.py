from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from review_summary.mcp import target_from_headers
from review_summary.query.review_state import ReviewState
from review_summary.services.summarizer import ReviewSummaryService

summaries = APIRouter(prefix="/review-summaries", tags=["Review summaries"])


class ReviewSummaryRequest(BaseModel):
    query: str = Field(description="Question to answer from the target reviews.")

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be empty")
        return value


@summaries.post("", response_model=ReviewState)
async def summarize_reviews(
    body: ReviewSummaryRequest,
    request: Request,
) -> ReviewState:
    try:
        target_id, target_type = target_from_headers(request.headers)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    service: ReviewSummaryService = request.app.state.review_summary_service
    return await service.summarize(body.query, target_id, target_type)
