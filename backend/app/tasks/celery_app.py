"""
Celery application configuration for async task processing.
"""
from celery import Celery

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "skillfit_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.resume_tasks", "app.tasks.match_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.batch_timeout_seconds,
    task_soft_time_limit=settings.batch_timeout_seconds - 30,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)
