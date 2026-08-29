from types import SimpleNamespace
from typing import Any, cast

import pytest
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams

from chat.agent.remote_agent import RemoteAgentsFactory
from chat.agent.review_summary_mcp import (
    create_review_summary_toolset,
    resolve_review_summary_url,
    review_summary_headers,
)


def test_review_summary_headers_use_the_single_mounted_review_target() -> None:
    context = cast(
        ReadonlyContext,
        SimpleNamespace(
            state={
                "_ag_ui_context": [
                    {
                        "description": "review target context",
                        "value": '{"targetId":"hotel-42","targetType":"hotel"}',
                    }
                ]
            }
        ),
    )

    assert review_summary_headers(context) == {
        "X-Review-Target-Id": "hotel-42",
        "X-Review-Target-Type": "hotel",
    }


def test_review_summary_headers_omit_untrusted_or_missing_target_context() -> None:
    context = cast(
        ReadonlyContext,
        SimpleNamespace(
            state={
                "_ag_ui_context": [
                    {
                        "description": "review target context",
                        "value": '{"targetId":"hotel-42","targetType":"hotel"}',
                    },
                    {
                        "description": "review target context",
                        "value": (
                            '{"targetId":"attraction-7","targetType":"attraction"}'
                        ),
                    },
                ]
            }
        ),
    )

    assert review_summary_headers(context) == {}


def test_review_summary_is_not_a_remote_a2a_agent() -> None:
    assert cast(Any, RemoteAgentsFactory)._DEFAULT_REMOTE_AGENTS == ["order_assistant"]


def test_review_summary_toolset_uses_streamable_http_mcp() -> None:
    toolset = create_review_summary_toolset()

    assert isinstance(toolset.connection_params, StreamableHTTPConnectionParams)
    assert toolset.connection_params.url.endswith("/mcp")
    assert toolset.tool_filter == ["summarize_reviews"]
    assert toolset.tool_name_prefix == "review_summary"
    assert toolset.header_provider is review_summary_headers


@pytest.mark.asyncio
async def test_review_summary_url_uses_nacos_ai_endpoint() -> None:
    class FakeNacosAI:
        async def get_mcp_server(self, name: str, version: str | None = None):
            assert name == "review-summary"
            return SimpleNamespace(
                frontendEndpoints=[
                    SimpleNamespace(
                        protocol="http",
                        address="review-summary",
                        port=24212,
                        path="/mcp",
                    )
                ]
            )

    url = await resolve_review_summary_url(FakeNacosAI(), "http://fallback:24212")

    assert url == "http://review-summary:24212/mcp"


@pytest.mark.asyncio
async def test_review_summary_url_falls_back_when_nacos_ai_discovery_fails() -> None:
    class FakeNacosAI:
        async def get_mcp_server(self, name: str, version: str | None = None):
            raise RuntimeError("nacos unavailable")

    url = await resolve_review_summary_url(FakeNacosAI(), "http://fallback:24212/")

    assert url == "http://fallback:24212/mcp"


@pytest.mark.asyncio
async def test_review_summary_url_accepts_nacos_backend_endpoint() -> None:
    class FakeNacosAI:
        async def get_mcp_server(self, name: str, version: str | None = None):
            return SimpleNamespace(
                backendEndpoints=[
                    SimpleNamespace(
                        protocol="https",
                        address="review-summary.internal",
                        port=443,
                    )
                ]
            )

    url = await resolve_review_summary_url(FakeNacosAI(), "http://fallback:24212")

    assert url == "https://review-summary.internal:443/mcp"


@pytest.mark.asyncio
async def test_review_summary_url_resolves_nacos_service_reference() -> None:
    class FakeNacosAI:
        async def get_mcp_server(self, name: str, version: str | None = None):
            return SimpleNamespace(
                remoteServerConfig=SimpleNamespace(
                    serviceRef=SimpleNamespace(
                        serviceName="trip-review-summary",
                        groupName="DEFAULT_GROUP",
                    ),
                    exportPath="/mcp",
                )
            )

    class FakeNaming:
        async def get_service_instance(
            self, service_name: str, group_name: str = "DEFAULT_GROUP"
        ):
            assert service_name == "trip-review-summary"
            assert group_name == "DEFAULT_GROUP"
            return SimpleNamespace(ip="review-summary", port=24212)

    url = await resolve_review_summary_url(
        FakeNacosAI(),
        "http://fallback:24212",
        nacos_naming=FakeNaming(),
    )

    assert url == "http://review-summary:24212/mcp"
