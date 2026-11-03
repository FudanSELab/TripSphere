import json
import logging
from collections.abc import Sequence
from typing import Any, Protocol

import httpx
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

from chat.agent.agui import extract_review_target
from chat.config.settings import get_settings

logger = logging.getLogger(__name__)

REVIEW_MCP_TIMEOUT_SECONDS = 60
REVIEW_MCP_TOOL_LIST_CACHE_TTL_SECONDS = 300


async def _log_mcp_request(request: httpx.Request) -> None:
    if request.url.path != "/mcp":
        return
    method = "unknown"
    try:
        payload = json.loads(request.content.decode("utf-8"))
        method = payload.get("method", method)
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    logger.info(
        "Review Summary MCP request method=%s http_method=%s session_id=%s",
        method,
        request.method,
        request.headers.get("mcp-session-id", "<none>"),
    )


async def _log_mcp_response(response: httpx.Response) -> None:
    if response.request.url.path != "/mcp":
        return
    logger.info(
        "Review Summary MCP response status=%s session_id=%s",
        response.status_code,
        response.headers.get(
            "mcp-session-id",
            response.request.headers.get("mcp-session-id", "<none>"),
        ),
    )


def review_summary_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers=headers,
        timeout=timeout,
        auth=auth,
        event_hooks={
            "request": [_log_mcp_request],
            "response": [_log_mcp_response],
        },
    )


class ReviewSummaryMcpToolset(McpToolset):
    def _tool_list_cache_key(self, headers: dict[str, str]) -> str | None:
        cache_headers = {
            name: value
            for name, value in headers.items()
            if name.lower() != "x-request-id"
        }
        return super()._tool_list_cache_key(cache_headers)


class McpDiscovery(Protocol):
    async def get_mcp_server(self, name: str, version: str | None = None) -> Any: ...


class ServiceDiscovery(Protocol):
    async def get_service_instance(
        self, service_name: str, group_name: str = "DEFAULT_GROUP"
    ) -> Any: ...


def review_summary_headers(context: ReadonlyContext) -> dict[str, str]:
    review_target = extract_review_target(context.state)
    headers = context.state.get("headers", {})
    request_id = headers.get("request_id") if isinstance(headers, dict) else None
    if not isinstance(request_id, str) or not request_id:
        request_id = None

    result: dict[str, str] = {}
    if request_id is not None:
        result["X-Request-ID"] = request_id
    if review_target is not None:
        result.update(
            {
                "X-Review-Target-Id": review_target.target_id,
                "X-Review-Target-Type": review_target.target_type,
            }
        )
    return result


async def resolve_review_summary_url(
    nacos_ai: McpDiscovery,
    fallback_url: str,
    *,
    service_name: str = "review-summary",
    version: str | None = None,
    nacos_naming: ServiceDiscovery | None = None,
) -> str:
    fallback = _mcp_url(fallback_url)
    try:
        server = await nacos_ai.get_mcp_server(service_name, version)
        endpoints = _server_endpoints(server)
        endpoint = _first_endpoint(endpoints)
        if endpoint is not None:
            protocol = getattr(endpoint, "protocol", None)
            address = getattr(endpoint, "address", None)
            port = getattr(endpoint, "port", None)
            path = getattr(endpoint, "path", None) or "/mcp"
            if protocol and address and port:
                return _mcp_url(f"{protocol}://{address}:{port}{path}")

        if nacos_naming is None:
            raise RuntimeError("Nacos MCP server has no discoverable endpoint")
        remote_config = getattr(server, "remoteServerConfig", None) or getattr(
            server, "remote_server_config", None
        )
        service_ref = getattr(remote_config, "serviceRef", None) or getattr(
            remote_config, "service_ref", None
        )
        naming_service_name = getattr(service_ref, "serviceName", None) or getattr(
            service_ref, "service_name", None
        )
        naming_group_name = getattr(service_ref, "groupName", None) or getattr(
            service_ref, "group_name", None
        ) or "DEFAULT_GROUP"
        if not naming_service_name:
            raise RuntimeError("Nacos MCP server has no service reference")
        instance = await nacos_naming.get_service_instance(
            naming_service_name, naming_group_name
        )
        address = getattr(instance, "ip", None) or getattr(instance, "address", None)
        port = getattr(instance, "port", None)
        path = getattr(remote_config, "exportPath", None) or getattr(
            remote_config, "export_path", None
        ) or "/mcp"
        if not address or not port:
            raise RuntimeError("Nacos service reference has no usable instance")
        return _mcp_url(f"http://{address}:{port}{path}")
    except Exception:
        logger.warning(
            "Falling back to configured Review Summary MCP URL", exc_info=True
        )
        return fallback


def create_review_summary_toolset(base_url: str | None = None) -> McpToolset:
    base_url = _mcp_url(base_url or get_settings().review_summary.url)
    return ReviewSummaryMcpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=base_url,
            timeout=REVIEW_MCP_TIMEOUT_SECONDS,
            httpx_client_factory=review_summary_http_client,
        ),
        tool_filter=["summarize_reviews"],
        tool_name_prefix="review_summary",
        header_provider=review_summary_headers,
        tool_list_cache_ttl_seconds=REVIEW_MCP_TOOL_LIST_CACHE_TTL_SECONDS,
    )


def _first_endpoint(endpoints: Sequence[Any] | None) -> Any | None:
    return next(iter(endpoints), None) if endpoints else None


def _server_endpoints(server: Any) -> Sequence[Any] | None:
    return (
        getattr(server, "frontendEndpoints", None)
        or getattr(server, "frontend_endpoints", None)
        or getattr(server, "backendEndpoints", None)
        or getattr(server, "backend_endpoints", None)
    )


def _mcp_url(url: str) -> str:
    normalized = url.rstrip("/")
    return normalized if normalized.endswith("/mcp") else f"{normalized}/mcp"
