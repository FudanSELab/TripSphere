"""Celery Worker standalone entrypoint."""

import logging
from collections.abc import Mapping
from contextvars import Token
from typing import cast

from celery import Celery
from celery.signals import (
    before_task_publish,
    setup_logging as celery_setup_logging,
    task_postrun,
    task_prerun,
)
from opentelemetry import propagate
from opentelemetry.context import Context, attach, detach

from review_summary.config.logging import setup_logging
from review_summary.config.settings import get_settings
from review_summary.correlation import (
    clear_current_request_id,
    set_current_request_id,
)

logger = logging.getLogger(__name__)

setup_logging()

_TRACE_CONTEXT_HEADER_NAMES = frozenset({"traceparent", "tracestate", "baggage"})


@celery_setup_logging.connect
def configure_celery_logging(**_: object) -> None:
    setup_logging()


@before_task_publish.connect
def inject_task_trace_context(
    headers: dict[str, object] | None = None, **_: object
) -> None:
    if headers is None:
        return

    carrier: dict[str, str] = {}
    propagate.inject(carrier)
    headers.update(carrier)


@task_prerun.connect
def bind_task_request_id(task: object, **_: object) -> None:
    task_request = cast(object | None, getattr(task, "request", None))
    headers = task_headers(task_request)
    request_id = headers.get("request_id") or headers.get("x-request-id")
    if request_id is None:
        args = task_args(task_request)
        if args and isinstance(args[0], Mapping):
            context = cast(Mapping[str, object], args[0])
            request_id = context.get("request_id")
    set_current_request_id(request_id)
    bind_task_trace_context(task_request, headers)


@task_postrun.connect
def clear_task_context(task: object | None = None, **_: object) -> None:
    task_request = (
        cast(object | None, getattr(task, "request", None))
        if task is not None
        else None
    )
    context_token = cast(
        Token[Context] | None,
        getattr(task_request, "_otel_context_token", None),
    )
    if context_token is not None:
        detach(context_token)
        delattr(task_request, "_otel_context_token")
    clear_current_request_id()


def task_headers(task_request: object | None) -> Mapping[str, object]:
    if task_request is None:
        return {}
    headers = cast(object, getattr(task_request, "headers", None))
    if isinstance(headers, Mapping):
        return cast(Mapping[str, object], headers)
    return {}


def task_args(task_request: object | None) -> tuple[object, ...]:
    if task_request is None:
        return ()
    args = cast(object, getattr(task_request, "args", ()))
    if isinstance(args, tuple):
        return cast(tuple[object, ...], args)
    if isinstance(args, list):
        return tuple(cast(list[object], args))
    return ()


def bind_task_trace_context(
    task_request: object | None, headers: Mapping[str, object]
) -> None:
    if task_request is None:
        return
    carrier: dict[str, str] = {}
    for key, value in headers.items():
        normalized_key = key.lower()
        if normalized_key in _TRACE_CONTEXT_HEADER_NAMES and value is not None:
            carrier[normalized_key] = str(value)
    if not carrier:
        return

    context_token = attach(propagate.extract(carrier))
    setattr(task_request, "_otel_context_token", context_token)


INDEX_TASK_MODULES = (
    "review_summary.index.tasks.collect_text_units",
    "review_summary.index.tasks.extract_graph",
    "review_summary.index.tasks.finalize_graph",
    "review_summary.index.tasks.create_communities",
    "review_summary.index.tasks.create_final_text_units",
    "review_summary.index.tasks.create_community_reports",
    "review_summary.index.tasks.create_text_embeddings",
)


def create_celery_app() -> Celery:
    """Create and configure a Celery application."""
    settings = get_settings()
    celery_app = Celery(
        settings.app.name,
        broker=settings.celery.broker_url,
        backend=settings.celery.result_backend,
        include=INDEX_TASK_MODULES,
    )
    celery_app.set_default()
    celery_app.conf.update(
        task_track_started=True,
        task_send_sent_event=True,
        worker_send_task_events=True,
        worker_hijack_root_logger=False,
        worker_redirect_stdouts=False,
    )
    return celery_app


app = create_celery_app()
