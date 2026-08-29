from typing import Any, cast

import pytest
from mcp.server.fastmcp import Context
from mcp.shared.context import RequestContext
from starlette.requests import Request

from review_summary.clients.reviews import TargetType
from review_summary.mcp import create_review_summary_mcp_server, target_from_headers
from review_summary.query.review_state import ReviewState
from review_summary.services.summarizer import ReviewSummaryService


def test_target_from_headers_requires_a_supported_mounted_target() -> None:
    target_id, target_type = target_from_headers(
        {
            "X-Review-Target-Id": "hotel-42",
            "X-Review-Target-Type": "hotel",
        }
    )

    assert target_id == "hotel-42"
    assert target_type is TargetType.HOTEL

    with pytest.raises(ValueError, match="mounted review target"):
        target_from_headers({})


@pytest.mark.asyncio
async def test_mcp_tool_accepts_only_the_user_query() -> None:
    mcp_server = create_review_summary_mcp_server(
        cast(Any, lambda: cast(ReviewSummaryService, object()))
    )

    tools = await mcp_server.list_tools()

    assert len(tools) == 1
    assert tools[0].name == "summarize_reviews"
    assert set(tools[0].inputSchema["properties"]) == {"query"}
    transport_security = mcp_server.settings.transport_security
    assert transport_security is not None
    assert "trip-review-summary:*" in transport_security.allowed_hosts


@pytest.mark.asyncio
async def test_mcp_tool_uses_the_request_target_headers() -> None:
    class RecordingService:
        async def summarize(
            self, query: str, target_id: str, target_type: TargetType
        ) -> ReviewState:
            assert query == "隔音怎么样？"
            assert target_id == "hotel-42"
            assert target_type is TargetType.HOTEL
            return ReviewState(
                status="empty_reviews",
                target_id=target_id,
                target_type=target_type,
                review_snapshot="snapshot",
                message="该目标目前还没有评论。",
            )

    service = cast(ReviewSummaryService, RecordingService())
    mcp_server = create_review_summary_mcp_server(lambda: service)
    tool_manager = getattr(mcp_server, "_tool_manager")
    tool = getattr(tool_manager, "_tools")["summarize_reviews"]
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "headers": [
                (b"x-review-target-id", b"hotel-42"),
                (b"x-review-target-type", b"hotel"),
            ],
        }
    )
    request_context: RequestContext[Any, None, Request] = RequestContext(
        request_id="test-request",
        meta=None,
        session=cast(Any, None),
        lifespan_context=None,
        request=request,
    )
    context: Context[Any, None, Request] = Context(
        request_context=request_context,
        fastmcp=mcp_server,
    )

    payload = await tool.fn("隔音怎么样？", context)

    assert payload["status"] == "empty_reviews"
