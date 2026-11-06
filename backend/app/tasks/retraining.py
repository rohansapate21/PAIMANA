"""
SIH 2026 — PS26103 | Model Retraining Celery Task
=================================================
Automates feature engineering, training of XGBoost (Cost) and LightGBM (Delay) models,
re-calculating composite risk scores and rules, and updating database tables.
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


@celery_app.task(bind=True, name="backend.app.tasks.retraining.run_retraining")
def run_retraining(self):
    """
    Executes the continuous machine learning retraining pipeline:
    1. ml/features/build_features.py
    2. ml/training/train_cost_model.py
    3. ml/training/train_delay_model.py
    4. ml/training/generate_risk_scores.py
    5. db.loader.py (refreshes risk_scores and alerts in PostgreSQL/SQLite)
    """
    logger.info("Starting automated ML retraining pipeline task...")
    python_bin = sys.executable

    steps = [
        ("Feature Engineering", [python_bin, "-m", "ml.features.build_features"]),
        ("Cost Model Training (XGBoost)", [python_bin, "-m", "ml.training.train_cost_model"]),
        ("Delay Model Training (LightGBM)", [python_bin, "-m", "ml.training.train_delay_model"]),
        ("Composite Risk & Rules Engine", [python_bin, "-m", "ml.training.generate_risk_scores"]),
    ]

    try:
        for step_name, cmd in steps:
            logger.info(f"Executing: {step_name}...")
            subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))

        logger.info("Updating database with newly generated risk scores and alerts...")
        run_loader()

        logger.info("ML retraining pipeline completed successfully.")
        return {
            "status": "SUCCESS",
            "task_id": self.request.id,
            "completed_at": datetime.utcnow().isoformat(),
            "message": "Model retraining and scoring refresh completed successfully."
        }
    except Exception as e:
        logger.error(f"Retraining pipeline failed: {e}")
        return {
            "status": "FAILED",
            "task_id": self.request.id,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }

