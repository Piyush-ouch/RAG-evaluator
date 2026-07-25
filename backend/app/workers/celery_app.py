"""
Celery Application Configuration

Configures Celery with Redis broker, task routing, and serialization.
"""

from __future__ import annotations

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "rageval",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing — different queues for different workloads
    task_routes={
        "app.workers.tasks.evaluation_tasks.*": {"queue": "evaluation"},
        "app.workers.tasks.report_tasks.*": {"queue": "reports"},
        "app.workers.tasks.data_tasks.*": {"queue": "data"},
        "app.workers.tasks.notification_tasks.*": {"queue": "notifications"},
    },

    # Default queue
    task_default_queue="default",

    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Result expiry
    result_expires=86400,  # 24 hours

    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-expired-data": {
            "task": "app.workers.tasks.maintenance_tasks.cleanup_expired",
            "schedule": 3600.0,  # Every hour
        },
    },
)

# Auto-discover tasks in all task modules
celery_app.autodiscover_tasks([
    "app.workers.tasks",
])
