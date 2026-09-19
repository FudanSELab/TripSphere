from __future__ import annotations

import os
import resource
import time
from collections.abc import Iterable

from opentelemetry import metrics
from opentelemetry.metrics import CallbackOptions, Observation
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "trip-review-summary")
_SERVICE_NAMESPACE = "tripsphere"
_DEPLOYMENT_ENVIRONMENT = os.getenv("APP_ENV", "local")
_STARTED_AT = time.monotonic()
_METER = metrics.get_meter("tripsphere.python")
_INSTRUMENTS: list[object] = []
_RUNTIME_CONFIGURED = False
_TASK_STARTED_AT: dict[str, float] = {}

_HTTP_REQUESTS = _METER.create_counter(
    "tripsphere.python.http.server.requests",
    unit="1",
    description="HTTP requests handled by the Python service.",
)
_HTTP_DURATION = _METER.create_histogram(
    "tripsphere.python.http.server.duration",
    unit="s",
    description="HTTP server request duration.",
)
_CELERY_TASKS = _METER.create_counter(
    "tripsphere.python.celery.task.executions",
    unit="1",
    description="Celery task executions handled by the worker.",
)
_CELERY_TASK_DURATION = _METER.create_histogram(
    "tripsphere.python.celery.task.duration",
    unit="s",
    description="Celery task execution duration.",
)


def _attrs(extra: dict[str, str | int] | None = None) -> dict[str, str | int]:
    attributes: dict[str, str | int] = {
        "service.name": _SERVICE_NAME,
        "service.namespace": _SERVICE_NAMESPACE,
        "deployment.environment.name": _DEPLOYMENT_ENVIRONMENT,
    }
    if extra:
        attributes.update(extra)
    return attributes


def _observe_uptime(_: CallbackOptions) -> Iterable[Observation]:
    yield Observation(time.monotonic() - _STARTED_AT, _attrs())


def _observe_rss(_: CallbackOptions) -> Iterable[Observation]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    yield Observation(usage.ru_maxrss * 1024, _attrs())


def _observe_cpu_time(_: CallbackOptions) -> Iterable[Observation]:
    process_times = os.times()
    yield Observation(process_times.user + process_times.system, _attrs())


def configure_runtime_metrics() -> None:
    global _RUNTIME_CONFIGURED
    if _RUNTIME_CONFIGURED:
        return

    _INSTRUMENTS.extend(
        [
            _METER.create_observable_gauge(
                "tripsphere.python.process.uptime",
                callbacks=[_observe_uptime],
                unit="s",
                description="Python process uptime.",
            ),
            _METER.create_observable_gauge(
                "tripsphere.python.process.memory.rss",
                callbacks=[_observe_rss],
                unit="By",
                description="Python process max RSS.",
            ),
            _METER.create_observable_gauge(
                "tripsphere.python.process.cpu.time",
                callbacks=[_observe_cpu_time],
                unit="s",
                description="Python process CPU time.",
            ),
        ]
    )
    _RUNTIME_CONFIGURED = True


class PythonMetricsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method", "UNKNOWN"))
        status_code = 500
        started_at = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 500))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            attributes = _attrs(
                {
                    "http.method": method,
                    "http.status_code": status_code,
                }
            )
            _HTTP_REQUESTS.add(1, attributes)
            _HTTP_DURATION.record(time.perf_counter() - started_at, attributes)


def record_task_start(task_id: str | None) -> None:
    if task_id:
        _TASK_STARTED_AT[task_id] = time.perf_counter()


def record_task_finish(
    task_id: str | None,
    task_name: str,
    state: str,
) -> None:
    started_at = _TASK_STARTED_AT.pop(task_id, None) if task_id else None
    attributes = _attrs({"celery.task_name": task_name, "celery.state": state})
    _CELERY_TASKS.add(1, attributes)
    if started_at is not None:
        _CELERY_TASK_DURATION.record(time.perf_counter() - started_at, attributes)
