from __future__ import annotations

from typing import Any

from celery import Task, shared_task


@shared_task(bind=True)
def run_workflow(self: Task[Any, Any], context: dict[str, Any]) -> dict[str, Any]:
    return context
