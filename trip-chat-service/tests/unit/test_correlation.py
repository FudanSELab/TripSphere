from __future__ import annotations

import logging
from uuid import UUID

import pytest
from starlette.types import Message, Receive, Scope, Send

from chat.correlation import (
    RequestCorrelationMiddleware,
    clear_current_request_id,
    get_current_request_id,
)


@pytest.mark.asyncio
async def test_request_correlation_middleware_preserves_and_returns_request_id() -> None:
    captured_request_ids: list[str | None] = []
    response_messages: list[Message] = []

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        captured_request_ids.append(get_current_request_id())
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def send(message: Message) -> None:
        response_messages.append(message)

    scope: Scope = {
        "type": "http",
        "headers": [(b"x-request-id", b"request-42")],
    }

    async def receive() -> Message:
        return {"type": "http.disconnect"}

    await RequestCorrelationMiddleware(app)(scope, receive, send)

    assert captured_request_ids == ["request-42"]
    assert response_messages[0]["headers"] == [(b"x-request-id", b"request-42")]
    assert get_current_request_id() is None


@pytest.mark.asyncio
async def test_request_correlation_middleware_generates_request_id() -> None:
    captured_request_ids: list[str | None] = []
    response_messages: list[Message] = []

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        captured_request_ids.append(get_current_request_id())
        await send({"type": "http.response.start", "status": 200, "headers": []})

    async def send(message: Message) -> None:
        response_messages.append(message)

    async def receive() -> Message:
        return {"type": "http.disconnect"}

    await RequestCorrelationMiddleware(app)(
        {"type": "http", "headers": []}, receive, send
    )

    request_id = captured_request_ids[0]
    assert request_id is not None
    UUID(request_id)
    assert response_messages[0]["headers"] == [
        (b"x-request-id", request_id.encode("ascii"))
    ]


def test_request_id_log_filter_uses_dash_without_context() -> None:
    from chat.correlation import RequestIdLogFilter

    clear_current_request_id()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="message",
        args=(),
        exc_info=None,
    )

    assert RequestIdLogFilter().filter(record)
    assert getattr(record, "request_id") == "-"
