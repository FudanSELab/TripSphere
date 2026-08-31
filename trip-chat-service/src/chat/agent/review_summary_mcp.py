import logging
from collections.abc import Sequence
from typing import Any, Protocol

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

from chat.agent.agui import extract_review_target
from chat.config.settings import get_settings

logger = logging.getLogger(__name__)


class McpDiscovery(Protocol):
    async def get_mcp_server(self, name: str, version: str | None = None) -> Any: ...


class ServiceDiscovery(Protocol):
    async def get_service_instance(
        self, service_name: str, group_name: str = "DEFAULT_GROUP"
    ) -> Any: ...


def review_summary_headers(context: ReadonlyContext) -> dict[str, str]:
    review_target = extract_review_target(context.state)
    if review_target is None:
        return {}
    return {
        "X-Review-Target-Id": review_target.target_id,
        "X-Review-Target-Type": review_target.target_type,
    }


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
            if not protocol or not address or not port:
                raise RuntimeError("Nacos MCP endpoint is incomplete")
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
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=base_url,
            timeout=15,
        ),
        tool_filter=["summarize_reviews"],
        tool_name_prefix="review_summary",
        header_provider=review_summary_headers,
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
