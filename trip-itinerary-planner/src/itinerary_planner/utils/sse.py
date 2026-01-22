import io
import re

_LINE_BREAK_RE = re.compile(r"\r\n|\r|\n")
DEFAULT_SEPARATOR = "\r\n"


def encode(
    data: str | None = "",
    event: str | None = None,
    event_id: str | None = None,
    comment: str | None = None,
    retry: int | None = None,
) -> str:
    buffer = io.StringIO()
    if comment is not None:
        for chunk in _LINE_BREAK_RE.split(comment):
            buffer.write(f": {chunk}")
            buffer.write(DEFAULT_SEPARATOR)

    if event_id is not None:
        buffer.write(_LINE_BREAK_RE.sub("", f"id: {event_id}"))
        buffer.write(DEFAULT_SEPARATOR)

    if event is not None:
        buffer.write(_LINE_BREAK_RE.sub("", f"event: {event}"))
        buffer.write(DEFAULT_SEPARATOR)

    if data is not None:
        for chunk in _LINE_BREAK_RE.split(data):
            buffer.write(f"data: {chunk}")
            buffer.write(DEFAULT_SEPARATOR)

    if retry is not None:
        buffer.write(f"retry: {retry}")
        buffer.write(DEFAULT_SEPARATOR)

    # SSE requires an empty line to mark the end of an event
    buffer.write(DEFAULT_SEPARATOR)

    return buffer.getvalue()
