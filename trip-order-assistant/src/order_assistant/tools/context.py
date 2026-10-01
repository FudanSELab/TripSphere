import logging
from contextvars import ContextVar
from typing import TypeAlias
from uuid import uuid4

from google.adk.tools.tool_context import ToolContext

GrpcMetadata: TypeAlias = tuple[tuple[str, str], ...]
_request_id: ContextVar[str | None] = ContextVar("order_assistant_request_id", default=None)


class CorrelationLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get() or "-"
        return True


def set_current_request_id(request_id: object) -> str:
    value = request_id.strip() if isinstance(request_id, str) else ""
    if not value or len(value) > 128 or any(ord(char) < 0x20 for char in value):
        value = str(uuid4())
    _request_id.set(value)
    return value


def get_current_request_id(tool_context: ToolContext) -> str:
    headers = tool_context.state.get("headers", {})
    value = headers.get("request_id") if isinstance(headers, dict) else None
    if isinstance(value, str) and value:
        return set_current_request_id(value)
    return _request_id.get() or set_current_request_id(None)


def get_current_user_id(tool_context: ToolContext) -> str | None:
    user_id = tool_context.state.get("headers", {}).get("user_id")
    return user_id if isinstance(user_id, str) and user_id else None


def build_grpc_metadata(
    tool_context: ToolContext, request_id: str | None = None
) -> GrpcMetadata:
    headers = tool_context.state.get("headers", {})
    correlation_request_id = set_current_request_id(
        request_id
        or (headers.get("request_id") if isinstance(headers, dict) else None)
        or _request_id.get()
    )
    metadata = (
        ("x-user-id", headers.get("user_id")),
        ("x-user-roles", headers.get("user_roles")),
        ("authorization", headers.get("authorization")),
        ("x-request-id", correlation_request_id),
    )
    return tuple(
        (key, value)
        for key, value in metadata
        if isinstance(value, str) and value
    )
