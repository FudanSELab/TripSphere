import json
import logging
from collections.abc import Callable, Mapping
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from review_summary.clients.reviews import TargetType
from review_summary.infra.nacos.utils import get_local_ip
from review_summary.services.summarizer import ReviewSummaryService

logger = logging.getLogger(__name__)

_TARGET_ID_HEADER = "x-review-target-id"
_TARGET_TYPE_HEADER = "x-review-target-type"
_MCP_ALLOWED_HOSTS = (
    "127.0.0.1:*",
    "localhost:*",
    "[::1]:*",
    "trip-review-summary:*",
)
_MCP_ALLOWED_ORIGINS = (
    "http://127.0.0.1:*",
    "http://localhost:*",
    "http://[::1]:*",
    "http://trip-review-summary:*",
)


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
    allowed_hosts = [*_MCP_ALLOWED_HOSTS, f"{get_local_ip()}:*"]
    server = FastMCP(
        name="review-summary",
        instructions=(
            "Summarize reviews for the target mounted in the current TripSphere "
            "page. The target is provided by trusted request headers."
        ),
        streamable_http_path="/mcp",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=list(_MCP_ALLOWED_ORIGINS),
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


class McpDiagnosticsMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http" or scope.get("path") != "/mcp":
            await self.app(scope, receive, send)
            return

        request_body = bytearray()
        response_status: int | None = None
        response_session_id: str | None = None

        async def diagnostic_receive() -> dict[str, Any]:
            message = await receive()
            if message["type"] == "http.request":
                request_body.extend(message.get("body", b""))
            return message

        async def diagnostic_send(message: dict[str, Any]) -> None:
            nonlocal response_status, response_session_id
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = dict(message.get("headers", []))
                raw_session_id = response_headers.get(b"mcp-session-id")
                response_session_id = (
                    raw_session_id.decode("utf-8", errors="replace")
                    if raw_session_id
                    else None
                )
            await send(message)

        try:
            await self.app(scope, diagnostic_receive, diagnostic_send)
        finally:
            request_headers = dict(scope.get("headers", []))
            raw_session_id = request_headers.get(b"mcp-session-id")
            request_session_id = (
                raw_session_id.decode("utf-8", errors="replace")
                if raw_session_id
                else None
            )
            method = "unknown"
            try:
                method = json.loads(request_body).get("method", method)
            except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                pass
            logger.info(
                "MCP HTTP exchange method=%s http_method=%s status=%s "
                "request_session_id=%s response_session_id=%s",
                method,
                scope.get("method", ""),
                response_status,
                request_session_id or "<none>",
                response_session_id or "<none>",
            )
