"""
SIH 2026 — PS26103 | Phase 2: Data Validation
=============================================
Runs basic data quality, referential integrity, and Pandera schema validation
on the master datasets.

Usage:
    python data/scripts/validate_master.py
"""

from pathlib import Path
import sys
import pandas as pd
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.validation.schemas import ProjectMasterSchema, PanelSchema

MASTER_DIR = PROJECT_ROOT / "data" / "master"

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")


def main():
    master_path = MASTER_DIR / "project_master.parquet"
    panel_path = MASTER_DIR / "project_month_panel.parquet"
    
    if not master_path.exists() or not panel_path.exists():
        logger.error("Master datasets not found. Run clean_master.py first.")
        return
        
    master = pd.read_parquet(master_path)
    panel = pd.read_parquet(panel_path)
    
    logger.info("=" * 60)
    logger.info("--- Data Quality & Validation Report ---")
    logger.info("=" * 60)
    
    # 1. Pandera Schema Validation
    logger.info("Running Pandera schema validation...")
    try:
        ProjectMasterSchema.validate(master)
        logger.info("[PASS] ProjectMasterSchema validation passed.")
    except Exception as e:
        logger.error(f"[FAIL] ProjectMasterSchema validation failed: {e}")
        
    try:
        PanelSchema.validate(panel)
        logger.info("[PASS] PanelSchema validation passed.")
    except Exception as e:
        logger.error(f"[FAIL] PanelSchema validation failed: {e}")
        
    # 2. Referential Integrity
    master_uids = set(master['project_uid'])
    panel_uids = set(panel['project_uid'])
    missing_in_master = panel_uids - master_uids
    if len(missing_in_master) == 0:
        logger.info("[PASS] Referential Integrity: All panel IDs exist in master table.")
    else:
        logger.warning(f"[FAIL] Referential Integrity: {len(missing_in_master)} panel IDs missing from master table.")
        
    # 3. Duplicate Checks
    master_dups = master.duplicated(subset=['project_uid']).sum()
    logger.info(f"Master Duplicates (should be 0): {master_dups}")
    
    panel_dups = panel.duplicated(subset=['project_uid', 'report_month']).sum()
    logger.info(f"Panel Duplicates (UID x Month) (should be 0): {panel_dups}")
    
    # 4. Basic Stats
    logger.info(f"Total Unique Projects Tracked: {len(master)}")
    logger.info(f"Total Monthly Observations: {len(panel)}")
    
    # 5. Null Checks on Key Fields
    critical_nulls = panel['revised_cost_cr'].isnull().sum()
    logger.info(f"Nulls in Revised Cost (Panel): {critical_nulls} ({critical_nulls/len(panel)*100:.1f}%)")
    
    progress_nulls = panel['physical_progress_pct'].isnull().sum()
    logger.info(f"Nulls in Physical Progress (Panel): {progress_nulls} ({progress_nulls/len(panel)*100:.1f}%)")
    
    # 6. Feature Stats
    imputed_prog = panel['is_imputed_progress'].sum()
    outliers = panel['outlier_flag'].sum()
    delayed_obs = (panel['schedule_delay_months'] > 0).sum()
    logger.info(f"LOCF Imputed Progress Observations: {imputed_prog} ({imputed_prog/len(panel)*100:.1f}%)")
    logger.info(f"Flagged Outlier Observations: {outliers} ({outliers/len(panel)*100:.1f}%)")
    logger.info(f"Delayed Observations (Schedule Delay > 0): {delayed_obs} ({delayed_obs/len(panel)*100:.1f}%)")
    
    logger.info("=" * 60)
    logger.info("Validation complete.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
