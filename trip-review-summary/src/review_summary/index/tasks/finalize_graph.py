from typing import Any

from asgiref.sync import async_to_sync
from celery import Task, shared_task

from review_summary.config.index.finalize_graph_config import FinalizeGraphConfig


@shared_task(bind=True)
def run_workflow(
    self: Task[Any, Any], context: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    async_to_sync(_finalize_graph)(
        self, context, FinalizeGraphConfig.model_validate(config)
    )
    return context


async def _finalize_graph(
    task: Task[Any, Any], context: dict[str, Any], config: FinalizeGraphConfig
) -> None:
    entities_filename = context["entities"]
    relationships_filename = context["relationships"]
    
