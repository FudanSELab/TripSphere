from __future__ import annotations

import logging
from contextvars import ContextVar, Token
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_REQUEST_ID = ContextVar[str | None]("chat_request_id", default=None)
_MAX_REQUEST_ID_LENGTH = 128


def normalize_request_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    request_id = value.strip()
    if not request_id or len(request_id) > _MAX_REQUEST_ID_LENGTH:
        return None
    if any(not 0x21 <= ord(character) <= 0x7E for character in request_id):
        return None
    return request_id


def new_request_id() -> str:
    return str(uuid4())


def get_current_request_id() -> str | None:
    return _REQUEST_ID.get()


def set_current_request_id(value: object) -> str | None:
    request_id = normalize_request_id(value)
    _REQUEST_ID.set(request_id)
    return request_id


def clear_current_request_id() -> None:
    _REQUEST_ID.set(None)


class RequestIdLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_current_request_id() or "-"
        return True


class RequestCorrelationMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _request_id_from_scope(scope) or new_request_id()
        token: Token[str | None] = _REQUEST_ID.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            _REQUEST_ID.reset(token)


def _request_id_from_scope(scope: Scope) -> str | None:
    for name, value in scope.get("headers", []):
        if name.lower() != b"x-request-id":
            continue
        try:
            return normalize_request_id(value.decode("ascii"))
        except UnicodeDecodeError:
            return None
    return None
