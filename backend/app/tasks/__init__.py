"""
SIH 2026 — PS26103 | Celery Tasks Package
"""

from backend.app.tasks.ingestion import run_ingestion_pipeline
from backend.app.tasks.retraining import run_retraining

__all__ = [
    "run_ingestion_pipeline",
    "run_retraining",
]

