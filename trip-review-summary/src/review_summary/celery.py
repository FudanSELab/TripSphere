"""Celery Worker standalone entrypoint."""

import logging

from celery import Celery

from review_summary.config.logging import setup_logging
from review_summary.config.settings import get_settings

logger = logging.getLogger(__name__)

setup_logging()


def create_celery_app() -> Celery:
    """Create and configure a Celery application."""
    settings = get_settings()
    celery_app = Celery(
        settings.app.name,
        broker=settings.celery.broker_url,
        backend=settings.celery.result_backend,
    )
    celery_app.set_default()
    # Autodiscover tasks from review_summary.index.tasks module
    celery_app.autodiscover_tasks(["review_summary.index.tasks"])
    celery_app.conf.update(task_track_started=True)
    return celery_app


app = create_celery_app()
