import pytest

from review_summary.clients.reviews import TargetType
from review_summary.query.base import SearchResult
from review_summary.query.review_state import ReviewPreflightResult
from review_summary.services.summarizer import ReviewSummaryService


class EmptyReviewSummaryService(ReviewSummaryService):
    def __init__(self) -> None:
        self.received_query: str | None = None

    async def _run_preflight(
        self, target_id: str, target_type: TargetType
    ) -> ReviewPreflightResult:
        return ReviewPreflightResult(
            status="empty_reviews",
            snapshot="empty-snapshot",
            reviews=[],
            message="该目标目前还没有评论。",
        )

    async def _execute_search(
        self,
        query: str,
        target_id: str,
        target_type: TargetType,
        review_snapshot: str,
    ) -> SearchResult:
        self.received_query = query
        raise AssertionError("search must not run when there are no reviews")


@pytest.mark.asyncio
async def test_summarize_returns_preflight_state_without_searching() -> None:
    service = EmptyReviewSummaryService()

    state = await service.summarize(
        query="  这家酒店隔音怎么样？  ",
        target_id="hotel-42",
        target_type=TargetType.HOTEL,
    )

    assert state.status == "empty_reviews"
    assert state.target_id == "hotel-42"
    assert state.target_type is TargetType.HOTEL
    assert state.review_snapshot == "empty-snapshot"
    assert service.received_query is None
