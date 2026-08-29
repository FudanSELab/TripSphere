from collections.abc import Callable, Mapping
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from review_summary.clients.reviews import TargetType
from review_summary.services.summarizer import ReviewSummaryService

_TARGET_ID_HEADER = "x-review-target-id"
_TARGET_TYPE_HEADER = "x-review-target-type"
_MCP_ALLOWED_HOSTS = [
    "127.0.0.1:*",
    "localhost:*",
    "[::1]:*",
    "trip-review-summary:*",
]
_MCP_ALLOWED_ORIGINS = [
    "http://127.0.0.1:*",
    "http://localhost:*",
    "http://[::1]:*",
    "http://trip-review-summary:*",
]


def target_from_headers(headers: Mapping[str, str]) -> tuple[str, TargetType]:
    target_id = _header_value(headers, _TARGET_ID_HEADER)
    target_type = _header_value(headers, _TARGET_TYPE_HEADER)
    if not target_id or not target_type:
        raise ValueError("A mounted review target is required")

    try:
        return target_id, TargetType(target_type)
    except ValueError as exc:
        raise ValueError("A supported mounted review target is required") from exc


def create_review_summary_mcp_server(
    service_provider: Callable[[], ReviewSummaryService],
) -> FastMCP:
    server = FastMCP(
        name="review-summary",
        instructions=(
            "Summarize reviews for the target mounted in the current TripSphere "
            "page. The target is provided by trusted request headers."
        ),
        streamable_http_path="/mcp",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=_MCP_ALLOWED_HOSTS,
            allowed_origins=_MCP_ALLOWED_ORIGINS,
        ),
    )

    @server.tool()
    async def summarize_reviews(  # pyright: ignore[reportUnusedFunction]
        query: str, context: Context[Any, Any, Any]
    ) -> dict[str, Any]:
        """Answer a question from the reviews of the currently mounted target."""
        request = context.request_context.request
        if request is None:
            raise ValueError("A mounted review target is required")

        target_id, target_type = target_from_headers(request.headers)
        state = await service_provider().summarize(
            query=query,
            target_id=target_id,
            target_type=target_type,
        )
        return state.to_payload()

    return server


def _header_value(headers: Mapping[str, str], name: str) -> str | None:
    for key, value in headers.items():
        if key.lower() == name:
            normalized_value = value.strip()
            return normalized_value or None
    return None
