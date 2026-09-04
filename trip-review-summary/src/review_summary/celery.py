"""Celery Worker standalone entrypoint."""

import logging

from celery import Celery

from review_summary.config.logging import setup_logging
from review_summary.config.settings import get_settings

logger = logging.getLogger(__name__)

setup_logging()

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
    celery_app.conf.update(task_track_started=True)
    return celery_app


app = create_celery_app()
