from __future__ import annotations

from types import SimpleNamespace

from opentelemetry import trace
from opentelemetry.context import attach, detach

from review_summary.celery import (
    bind_task_request_id,
    clear_task_context,
    inject_task_trace_context,
)
from review_summary.correlation import get_current_request_id

_TRACE_ID = 0x0102030405060708090A0B0C0D0E0F10
_SPAN_ID = 0x1112131415161718
_TRACEPARENT = "00-0102030405060708090a0b0c0d0e0f10-1112131415161718-01"


def test_inject_task_trace_context_adds_traceparent_header() -> None:
    span_context = trace.SpanContext(
        trace_id=_TRACE_ID,
        span_id=_SPAN_ID,
        is_remote=False,
        trace_flags=trace.TraceFlags(trace.TraceFlags.SAMPLED),
    )
    token = attach(trace.set_span_in_context(trace.NonRecordingSpan(span_context)))
    try:
        headers: dict[str, object] = {}
        inject_task_trace_context(headers=headers)
    finally:
        detach(token)

    assert headers["traceparent"] == _TRACEPARENT


def test_bind_task_request_id_extracts_trace_context_and_clears_it() -> None:
    task = SimpleNamespace(
        request=SimpleNamespace(
            headers={"request_id": "request-99", "traceparent": _TRACEPARENT}
        )
    )

    bind_task_request_id(task)

    assert get_current_request_id() == "request-99"
    assert trace.get_current_span().get_span_context().trace_id == _TRACE_ID

    clear_task_context(task)

    assert get_current_request_id() is None
    assert not trace.get_current_span().get_span_context().is_valid
