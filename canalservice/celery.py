import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "canalservice.settings")

app = Celery(
    "canalservice", broker="redis://127.0.0.1:6379//", backend="redis://127.0.0.1:6379"
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.

app.conf.beat_schedule = {
    "peridic_check": {
        "task": "googlesheet_check",
        "schedule": 5.0,
    }
}

app.autodiscover_tasks()
