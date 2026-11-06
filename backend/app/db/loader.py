"""
SIH 2026 — PS26103 | Phase 9: Database Population & Bulk Loader
===============================================================
Loads parquet and CSV artifacts into the relational database:
1. data/master/project_master.parquet -> project_master table
2. data/master/project_month_panel.parquet -> project_month_panel table
3. ml/eda_outputs/latest_risk_scores.csv -> risk_scores & explanations tables
4. Generates initial alerts for rule-triggered and high-risk projects -> alerts table
5. Seeds initial admin and analyst accounts -> users table
6. Logs the ingestion job -> ingestion_log table

Usage:
    python -m backend.app.db.loader
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger
from sqlalchemy import select, delete

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.session import SessionLocal, engine
from backend.app.models.project import (
    ProjectMaster,
    ProjectMonthPanel,
    RiskScore,
    Explanation,
    Alert,
    User,
    IngestionLog
)
from backend.app.core.security import get_password_hash

MASTER_PATH = PROJECT_ROOT / "data" / "master" / "project_master.parquet"
PANEL_PATH = PROJECT_ROOT / "data" / "master" / "project_month_panel.parquet"
SCORES_PATH = PROJECT_ROOT / "ml" / "eda_outputs" / "latest_risk_scores.csv"

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")


def seed_users(db):
    """Seed initial administrative and analyst users if not already present."""
    logger.info("Checking user accounts...")
    existing_admin = db.execute(select(User).where(User.email == "admin@mospi.gov.in")).scalar_one_or_none()
    
    if not existing_admin:
        admin_user = User(
            email="admin@mospi.gov.in",
            hashed_password=get_password_hash("Admin@123"),
            full_name="MoSPI Administrator",
            role="admin",
            ministry_scope=None,
            created_at=datetime.utcnow()
        )
        analyst_user = User(
            email="analyst@mospi.gov.in",
            hashed_password=get_password_hash("Analyst@123"),
            full_name="Infrastructure Analyst",
            role="analyst",
            ministry_scope=None,
            created_at=datetime.utcnow()
        )
        db.add_all([admin_user, analyst_user])
        db.commit()
        logger.info("Created default users: admin@mospi.gov.in and analyst@mospi.gov.in")
    else:
        logger.info("Default user accounts already initialized.")


def load_project_master(db):
    """Load project master entities from parquet."""
    if not MASTER_PATH.exists():
        logger.error(f"File not found: {MASTER_PATH}")
        return 0

    logger.info(f"Loading {MASTER_PATH.name}...")
    df = pd.read_parquet(MASTER_PATH)
    
    # Clean records
    records = []
    for _, row in df.iterrows():
        records.append({
            "project_uid": str(row["project_uid"]),
            "original_project_id": str(row.get("project_code", "") or ""),
            "project_name": str(row.get("project_name", "Unknown")),
            "implementing_agency": str(row.get("implementing_agency", "") or ""),
            "ministry": str(row.get("ministry", "Unknown")),
            "sector": str(row.get("sector", "Other")),
            "state": str(row.get("state", "Unknown")),
            "original_cost_cr": float(row.get("original_cost_cr", 0.0) or 0.0),
            "approval_date": str(row.get("approval_date", "") or ""),
            "start_date": str(row.get("start_date", "") or ""),
            "original_completion_date": str(row.get("original_completion_date", "") or ""),
            "date_precision": "month",
            "first_seen_report_month": str(row.get("first_seen_report_month", "") or ""),
            "last_seen_report_month": str(row.get("last_seen_report_month", "") or "")
        })
    
    # Clear existing and bulk insert
    db.execute(delete(ProjectMaster))
    db.bulk_insert_mappings(ProjectMaster, records)
    db.commit()
    logger.info(f"Loaded {len(records)} projects into project_master.")
    return len(records)


def load_project_panel(db):
    """Load longitudinal panel facts from parquet."""
    if not PANEL_PATH.exists():
        logger.error(f"File not found: {PANEL_PATH}")
        return 0

    logger.info(f"Loading {PANEL_PATH.name}...")
    df = pd.read_parquet(PANEL_PATH)
    
    records = []
    for _, row in df.iterrows():
        records.append({
            "project_uid": str(row["project_uid"]),
            "report_month": str(row["report_month"]),
            "revised_cost_cr": float(row.get("revised_cost_cr", 0.0) or 0.0),
            "expenditure_cr": float(row.get("expenditure_cr", 0.0) or 0.0) if pd.notna(row.get("expenditure_cr")) else 0.0,
            "physical_progress_pct": float(row.get("physical_progress_pct", 0.0) or 0.0),
            "delta_cost_cr": float(row.get("delta_cost_cr", 0.0) or 0.0),
            "delta_progress_pct": float(row.get("delta_progress_pct", 0.0) or 0.0),
            "progress_stagnation_streak": int(row.get("progress_stagnation_streak", 0) or 0),
            "cost_revision_count": int(row.get("cost_revision_count", 0) or 0),
            "schedule_delay_months": float(row.get("schedule_delay_months", 0.0) or 0.0),
            "is_imputed_cost": bool(row.get("is_imputed_cost", False)),
            "is_imputed_progress": bool(row.get("is_imputed_progress", False)),
            "outlier_flag": bool(row.get("outlier_flag", False))
        })
    
    db.execute(delete(ProjectMonthPanel))
    db.bulk_insert_mappings(ProjectMonthPanel, records)
    db.commit()
    logger.info(f"Loaded {len(records)} observations into project_month_panel.")
    return len(records)


def load_risk_scores_and_alerts(db):
    """Load risk scores, top explanations, and seed alerts."""
    if not SCORES_PATH.exists():
        logger.error(f"File not found: {SCORES_PATH}")
        return 0, 0

    logger.info(f"Loading {SCORES_PATH.name}...")
    df = pd.read_csv(SCORES_PATH)
    
    # 1. Clear old scores & alerts
    db.execute(delete(Explanation))
    db.execute(delete(Alert))
    db.execute(delete(RiskScore))
    db.commit()
    
    score_objs = []
    alert_objs = []
    
    for _, row in df.iterrows():
        p_uid = str(row["project_uid"])
        r_month = str(row["report_month"])
        score = float(row.get("risk_score", 0.0))
        band = str(row.get("risk_band", "Low"))
        ml_score = float(row.get("ml_risk_score", 0.0)) if pd.notna(row.get("ml_risk_score")) else None
        rule_score = float(row.get("rule_score", 0.0)) if pd.notna(row.get("rule_score")) else None
        rule_triggered = bool(row.get("rule_triggered", False))
        cost_prob = float(row.get("cost_risk_prob", 0.0)) if pd.notna(row.get("cost_risk_prob")) else None
        delay_prob = float(row.get("delay_risk_prob", 0.0)) if pd.notna(row.get("delay_risk_prob")) else None
        explanation = str(row.get("shap_explanation", "") or "")
        
        score_entry = RiskScore(
            project_uid=p_uid,
            report_month=r_month,
            risk_score=score,
            risk_band=band,
            ml_risk_score=ml_score,
            rule_score=rule_score,
            rule_triggered=rule_triggered,
            cost_risk_prob=cost_prob,
            delay_risk_prob=delay_prob,
            shap_explanation=explanation,
            model_version="v1.0",
            scored_at=datetime.utcnow()
        )
        score_objs.append(score_entry)
        
        # Check if an alert should be created for this project
        if band == "High" or rule_triggered:
            alert_type = "rule_triggered" if rule_triggered else "ml_high_risk"
            severity = "High" if (score >= 70.0 or rule_score >= 30.0) else "Medium"
            alert_entry = Alert(
                project_uid=p_uid,
                report_month=r_month,
                alert_type=alert_type,
                severity=severity,
                reason=explanation,
                created_at=datetime.utcnow(),
                acknowledged=False
            )
            alert_objs.append(alert_entry)

    db.add_all(score_objs)
    db.commit()
    logger.info(f"Loaded {len(score_objs)} risk scores into risk_scores.")
    
    # Save alerts
    db.add_all(alert_objs)
    db.commit()
    logger.info(f"Created {len(alert_objs)} proactive early warning alerts in alerts table.")
    
    return len(score_objs), len(alert_objs)


def run_loader():
    """Runs the full database loading process."""
    logger.info("=" * 60)
    logger.info("Starting Database Hydration from Parquet/CSV Artifacts...")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Seed users
        seed_users(db)
        
        # Ingest master & panel
        master_count = load_project_master(db)
        panel_count = load_project_panel(db)
        
        # Ingest scores & alerts
        scores_count, alerts_count = load_risk_scores_and_alerts(db)
        
        # Log ingestion summary
        latest_month = "2026-08-01"
        ingest_log = IngestionLog(
            report_month=latest_month,
            rows_extracted=panel_count,
            warnings_count=0,
            status="SUCCESS",
            run_at=datetime.utcnow()
        )
        db.add(ingest_log)
        db.commit()
        
        logger.info("=" * 60)
        logger.info("DATABASE HYDRATION COMPLETE:")
        logger.info(f"  - Users Seeded:           admin@mospi.gov.in / analyst@mospi.gov.in")
        logger.info(f"  - Projects (Master):      {master_count}")
        logger.info(f"  - Monthly Panel Records:  {panel_count}")
        logger.info(f"  - Scored Projects:        {scores_count}")
        logger.info(f"  - Proactive Alerts:       {alerts_count}")
        logger.info("=" * 60)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to load database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_loader()

