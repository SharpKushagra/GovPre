"""
Celery application setup and configuration.
"""
from celery import Celery
from celery.schedules import crontab

from backend.config import settings

celery_app = Celery(
    "govpreneurs",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["backend.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24 hours
)

# Celery Beat schedule — periodic tasks
celery_app.conf.beat_schedule = {
    # Poll SAM.gov every 6 hours
    "samgov-ingestion-every-6-hours": {
        "task": "backend.workers.tasks.ingest_samgov_opportunities",
        "schedule": settings.SAMGOV_POLL_INTERVAL,
    },
    # Mark expired opportunities daily at midnight
    "mark-expired-opportunities-daily": {
        "task": "backend.workers.tasks.mark_expired_opportunities",
        "schedule": crontab(hour=0, minute=0),
    },
}
