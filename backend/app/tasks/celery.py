from celery import Celery

from app.config import settings
import app.db.model_registry  # noqa: F401


celery_app = Celery(
    "inkris-main-worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# make sure the tasks to be discovered exist in __init__ file
celery_app.autodiscover_tasks(["app.tasks"])

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
