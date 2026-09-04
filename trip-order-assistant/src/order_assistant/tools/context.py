from typing import TypeAlias

from google.adk.tools.tool_context import ToolContext

GrpcMetadata: TypeAlias = tuple[tuple[str, str], ...]


def get_current_user_id(tool_context: ToolContext) -> str | None:
    user_id = tool_context.state.get("headers", {}).get("user_id")
    return user_id if isinstance(user_id, str) and user_id else None


def build_grpc_metadata(tool_context: ToolContext) -> GrpcMetadata:
    headers = tool_context.state.get("headers", {})
    metadata = (
        ("x-user-id", headers.get("user_id")),
        ("x-user-roles", headers.get("user_roles")),
        ("authorization", headers.get("authorization")),
    )
    return tuple(
        (key, value)
        for key, value in metadata
        if isinstance(value, str) and value
    )
