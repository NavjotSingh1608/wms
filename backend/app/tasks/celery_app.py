"""
Celery app and Beat schedule.
Broker and backend use REDIS_URL / CELERY_BROKER_URL from environment.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

broker = settings.CELERY_BROKER_URL or settings.REDIS_URL
backend = settings.REDIS_URL.replace("/0", "/1") if settings.REDIS_URL else "redis://localhost:6379/1"

celery_app = Celery(
    "wms",
    broker=broker,
    backend=backend,
    include=["app.tasks.alert_tasks"],
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

celery_app.conf.beat_schedule = {
    "daily-retest-alert": {
        "task": "app.tasks.alert_tasks.send_retest_alerts",
        "schedule": crontab(hour=8, minute=0),
    },
    "daily-expiry-alert": {
        "task": "app.tasks.alert_tasks.send_expiry_alerts",
        "schedule": crontab(hour=8, minute=0),
    },
}
