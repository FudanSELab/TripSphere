from __future__ import annotations

from typing import Any

from asgiref.sync import async_to_sync
from celery import Task, shared_task

from review_summary.config.query.create_static_summary_config import (
    CreateStaticSummaryConfig,
)


@shared_task(bind=True)
def run_workflow(
    self: Task[Any, Any], context: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    async_to_sync(_create_static_summary)(
        self, context, CreateStaticSummaryConfig.model_validate(config)
    )
    return context


async def _create_static_summary(
    task: Task[Any, Any], context: dict[str, Any], config: CreateStaticSummaryConfig
) -> None:
    """Create a static summary of the review."""
    raise NotImplementedError
