from types import SimpleNamespace
from typing import Any, cast

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams

from chat.agent.remote_agent import RemoteAgentsFactory
from chat.agent.review_summary_mcp import (
    create_review_summary_toolset,
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
                        "value": '{"targetId":"attraction-7","targetType":"attraction"}',
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
