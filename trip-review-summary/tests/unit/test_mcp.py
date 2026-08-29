import json
from typing import Any, cast

import pytest
from mcp.server.fastmcp import Context
from mcp.shared.context import RequestContext
from starlette.requests import Request
from v2.nacos.transport.grpc_util import GrpcUtils  # type: ignore

from review_summary.clients.reviews import TargetType
from review_summary.infra.nacos.ai import NacosAI
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
    tool_manager = mcp_server._tool_manager
    tool = tool_manager._tools["summarize_reviews"]
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


@pytest.mark.asyncio
async def test_nacos_ai_registers_review_summary_mcp_endpoint() -> None:
    class FakeAIService:
        def __init__(self) -> None:
            self.released = None

        async def release_mcp_server(self, param: Any) -> None:
            self.released = param
            return "mcp-id"

        async def get_mcp_server(self, param: Any) -> None:
            raise RuntimeError("not found")

    client = NacosAI("review-summary", 24212, "nacos:8848", "public", "1.0.0")
    service = FakeAIService()
    client.ai_service = cast(Any, service)

    await client.register_mcp_server()

    json.dumps(service.released, default=GrpcUtils.to_json)

    assert service.released.server_spec.name == "review-summary"
    assert service.released.server_spec.versionDetail.version == "1.0.0"
    assert service.released.server_spec.protocol == "mcp-streamable"
    assert service.released.server_spec.remoteServerConfig.exportPath == "/mcp"
    assert service.released.mcp_endpoint_spec.type == "REF"
    assert service.released.mcp_endpoint_spec.data == {
        "serviceName": "trip-review-summary",
        "groupName": "DEFAULT_GROUP",
        "namespaceId": "public",
    }


@pytest.mark.asyncio
async def test_nacos_ai_skips_release_for_existing_mcp_version() -> None:
    class FakeAIService:
        async def get_mcp_server(self, param: Any) -> object:
            return object()

        async def release_mcp_server(self, param: Any) -> None:
            raise AssertionError("existing MCP version was released again")

    client = NacosAI("review-summary", 24212, "nacos:8848", "public", "1.0.0")
    client.ai_service = cast(Any, FakeAIService())

    await client.register_mcp_server()
