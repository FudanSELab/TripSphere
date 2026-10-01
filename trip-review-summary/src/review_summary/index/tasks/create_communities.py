from __future__ import annotations

from typing import Any

from celery import Task, shared_task

from review_summary.correlation import set_current_request_id


@shared_task(bind=True)
def run_workflow(self: Task[Any, Any], context: dict[str, Any]) -> dict[str, Any]:
    set_current_request_id(context.get("request_id"))
    return context
