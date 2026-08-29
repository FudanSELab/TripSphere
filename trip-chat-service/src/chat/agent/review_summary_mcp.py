from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

from chat.agent.agui import extract_review_target
from chat.config.settings import get_settings


def review_summary_headers(context: ReadonlyContext) -> dict[str, str]:
    review_target = extract_review_target(context.state)
    if review_target is None:
        return {}
    return {
        "X-Review-Target-Id": review_target.target_id,
        "X-Review-Target-Type": review_target.target_type,
    }


def create_review_summary_toolset() -> McpToolset:
    base_url = get_settings().review_summary.url.rstrip("/")
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=f"{base_url}/mcp",
            timeout=15,
        ),
        tool_filter=["summarize_reviews"],
        tool_name_prefix="review_summary",
        header_provider=review_summary_headers,
    )
