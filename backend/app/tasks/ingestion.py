"""
SIH 2026 — PS26103 | Ingestion Celery Task
==========================================
Coordinates automated data extraction, cleaning, schema validation,
and database loading.
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.celery_app import celery_app
from backend.app.db.loader import run_loader


@celery_app.task(bind=True, name="backend.app.tasks.ingestion.run_ingestion_pipeline")
def run_ingestion_pipeline(self):
    """
    Executes the end-to-end data processing workflow:
    1. clean_master.py -> updates master parquet and panel parquet
    2. validate_master.py -> verifies pandera schema and constraints
    3. db.loader.py -> rehydrates database with newly validated data
    """
    logger.info("Starting automated ingestion pipeline task...")
    python_bin = sys.executable

    try:
        # Step 1: Clean master & panel
        clean_script = PROJECT_ROOT / "data" / "scripts" / "clean_master.py"
        if clean_script.exists():
            logger.info("Running data/scripts/clean_master.py...")
            subprocess.run([python_bin, str(clean_script)], check=True, cwd=str(PROJECT_ROOT))

        # Step 2: Validate master
        validate_script = PROJECT_ROOT / "data" / "scripts" / "validate_master.py"
        if validate_script.exists():
            logger.info("Running data/scripts/validate_master.py...")
            subprocess.run([python_bin, str(validate_script)], check=True, cwd=str(PROJECT_ROOT))

        # Step 3: Run database loader
        logger.info("Hydrating database via db.loader.run_loader()...")
        run_loader()

        logger.info("Ingestion pipeline completed successfully.")
        return {
            "status": "SUCCESS",
            "task_id": self.request.id,
            "completed_at": datetime.utcnow().isoformat(),
            "message": "Data ingestion and database hydration completed."
        }
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        return {
            "status": "FAILED",
            "task_id": self.request.id,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }

