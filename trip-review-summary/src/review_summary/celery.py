"""Celery Worker standalone entrypoint."""

import logging

from celery import Celery
from celery.signals import setup_logging as celery_setup_logging
from celery.signals import task_postrun, task_prerun

from review_summary.config.logging import setup_logging
from review_summary.config.settings import get_settings
from review_summary.metrics import (
    configure_runtime_metrics,
    record_task_finish,
    record_task_start,
)

logger = logging.getLogger(__name__)

setup_logging()
configure_runtime_metrics()


@celery_setup_logging.connect
def configure_celery_logging(**_: object) -> None:
    setup_logging()


@task_prerun.connect
def record_celery_task_start(task_id: str | None = None, **_: object) -> None:
    record_task_start(task_id)


@task_postrun.connect
def record_celery_task_finish(
    task_id: str | None = None,
    task: object | None = None,
    state: str | None = None,
    **_: object,
) -> None:
    task_name = getattr(task, "name", "unknown")
    record_task_finish(task_id, str(task_name), state or "unknown")


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
        worker_hijack_root_logger=False,
        worker_redirect_stdouts=False,
    )
    return celery_app


app = create_celery_app()
