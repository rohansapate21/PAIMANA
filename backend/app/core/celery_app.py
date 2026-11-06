"""
SIH 2026 — PS26103 | Celery Application Instance
=================================================
Configured with Redis broker and result backend for long-running batch workloads:
- Monthly data ingestion & PDF extraction
- ML feature pipeline & model retraining
"""

import sys
from pathlib import Path
from celery import Celery

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings

broker_url = settings.CELERY_BROKER_URL or "redis://localhost:6379/1"
backend_url = settings.CELERY_RESULT_BACKEND or "redis://localhost:6379/2"

celery_app = Celery(
    "paimana_tasks",
    broker=broker_url,
    backend=backend_url,
    include=[
        "backend.app.tasks.ingestion",
        "backend.app.tasks.retraining"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour maximum per pipeline run
    task_default_queue="default",
)

