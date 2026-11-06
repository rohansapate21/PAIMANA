"""
SIH 2026 — PS26103 | Phase 2: Clean and Panel Builder
=====================================================
Takes the merged long dataset, handles missing values, standardizes data types,
and computes time-series features (deltas, stagnation).
Splits output into `project_master` (static) and `project_month_panel` (time-series).

Usage:
    python data/scripts/clean_master.py
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

# ---------------------------------------------------------------------------
# Configuration & Mapping
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INTERIM_DIR = DATA_DIR / "interim"
MASTER_DIR = DATA_DIR / "master"

MASTER_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()
import sys
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")

# Mapping of the 17 canonical ministries (and aliases) to standard infrastructure sectors
MINISTRY_TO_SECTOR = {
    "Ministry of Road Transport and Highways": "Roads",
    "Ministry of Road Transport & Highways": "Roads",
    "Ministry of Railways": "Railways",
    "Ministry of Power": "Power",
    "Ministry of Housing and Urban Affairs": "Urban",
    "Ministry of Housing & Urban Affairs": "Urban",
    "Ministry of Water Resources / Jal Shakti": "Water",
    "Ministry of Jal Shakti": "Water",
    "Department of Water Resources, River Development & GR": "Water",
    "Department of Water Resources": "Water",
    "Ministry of Civil Aviation": "Aviation",
    "Ministry of Shipping / Ports, Shipping and Waterways": "Ports",
    "Ministry of Ports, Shipping and Waterways": "Ports",
    "Ministry of Coal": "Coal",
    "Ministry of Petroleum and Natural Gas": "Oil & Gas",
    "Ministry of Petroleum & Natural Gas": "Oil & Gas",
    "Ministry of Steel": "Steel",
    "Ministry of Defence": "Defence",
    "Department of Telecommunications": "Telecom",
    "Ministry of Communications": "Telecom",
    "Ministry of Health and Family Welfare": "Health",
    "Ministry of Health & Family Welfare": "Health",
    "Ministry of Mines": "Mines",
    "Ministry of New and Renewable Energy": "Renewable Energy",
    "Ministry of Commerce and Industry": "Other",
    "Ministry of Commerce & Industry": "Other",
    "Ministry of Information and Broadcasting": "Other",
    "Ministry of Science and Technology": "Other",
    "Department of Higher Education": "Other",
    "Department of Sports": "Other",
    "Ministry of Labour and Employment": "Other",
}


def derive_sector_from_ministry(ministry_raw: str) -> str:
    """Derive standard infrastructure sector from ministry name."""
    if not isinstance(ministry_raw, str) or not ministry_raw.strip():
        return "Other"
    
    clean_m = ministry_raw.strip()
    if clean_m in MINISTRY_TO_SECTOR:
        return MINISTRY_TO_SECTOR[clean_m]
    
    m_lower = clean_m.lower()
    if "road" in m_lower or "highway" in m_lower or "morth" in m_lower:
        return "Roads"
    if "railway" in m_lower:
        return "Railways"
    if "power" in m_lower:
        return "Power"
    if "petroleum" in m_lower or "gas" in m_lower or "oil" in m_lower:
        return "Oil & Gas"
    if "coal" in m_lower:
        return "Coal"
    if "telecom" in m_lower or "communication" in m_lower:
        return "Telecom"
    if "aviation" in m_lower or "airport" in m_lower:
        return "Aviation"
    if "port" in m_lower or "shipping" in m_lower or "waterway" in m_lower:
        return "Ports"
    if "water" in m_lower or "jal" in m_lower or "river" in m_lower:
        return "Water"
    if "housing" in m_lower or "urban" in m_lower:
        return "Urban"
    if "health" in m_lower:
        return "Health"
    if "steel" in m_lower:
        return "Steel"
    if "defence" in m_lower or "defense" in m_lower:
        return "Defence"
    if "mine" in m_lower:
        return "Mines"
    if "renewable" in m_lower:
        return "Renewable Energy"
        
    return "Other"


def compute_schedule_delay(df: pd.DataFrame) -> pd.DataFrame:
    """Compute schedule delay in months: (revised_doc - original_doc)."""
    logger.info("Computing schedule delay in months...")
    orig_dates = pd.to_datetime(df['original_completion_date'], format='%m/%Y', errors='coerce')
    rev_dates = pd.to_datetime(df['revised_completion_date'], format='%m/%Y', errors='coerce')
    
    delay = (rev_dates.dt.year * 12 + rev_dates.dt.month) - (orig_dates.dt.year * 12 + orig_dates.dt.month)
    df['schedule_delay_months'] = delay.clip(lower=0).fillna(0).astype('float32')
    return df


def apply_locf_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Last-Observation-Carried-Forward (LOCF) imputation.
    Forward-fill up to 2 consecutive missing months per project for revised_cost and progress.
    Flag imputed observations with companion boolean columns.
    """
    logger.info("Applying LOCF imputation (up to 2 months per project)...")
    df = df.sort_values(by=['project_uid', 'report_month'])
    
    # 1. Cost imputation
    was_na_cost = df['revised_cost_cr'].isna()
    df['revised_cost_cr'] = df.groupby('project_uid')['revised_cost_cr'].ffill(limit=2)
    df['is_imputed_cost'] = (was_na_cost & df['revised_cost_cr'].notna()).astype(bool)
    
    # 2. Progress imputation
    was_na_prog = df['physical_progress_pct'].isna()
    df['physical_progress_pct'] = df.groupby('project_uid')['physical_progress_pct'].ffill(limit=2)
    df['is_imputed_progress'] = (was_na_prog & df['physical_progress_pct'].notna()).astype(bool)
    
    # Fill remaining progress/cost nulls (if any) with 0.0 for stable modeling
    df['physical_progress_pct'] = df['physical_progress_pct'].fillna(0.0)
    df['revised_cost_cr'] = df['revised_cost_cr'].fillna(0.0)
    
    return df


def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Flag domain outliers without deleting rows."""
    logger.info("Flagging cost and progress outliers...")
    med_cost = df.groupby('ministry')['revised_cost_cr'].transform('median')
    outlier_cost = (df['revised_cost_cr'] > 50 * med_cost) & (med_cost > 0)
    outlier_prog = (df['physical_progress_pct'] > 100) | (df['physical_progress_pct'] < 0)
    df['outlier_flag'] = (outlier_cost | outlier_prog).astype(bool)
    return df


def _calc_streak_array(s_values: np.ndarray) -> np.ndarray:
    """Calculate consecutive stagnant streak resetting on progress."""
    streak = np.zeros(len(s_values), dtype=np.int32)
    curr = 0
    for i, val in enumerate(s_values):
        if val == 1:
            curr += 1
        else:
            curr = 0
        streak[i] = curr
    return streak


def create_panel_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute time-series features for each project."""
    logger.info("Computing time-series features (deltas, true stagnation streak)...")
    
    # Ensure temporal sorting within each project
    df = df.sort_values(by=['project_uid', 'report_month'])
    
    # Month-over-month deltas
    df['delta_cost_cr'] = df.groupby('project_uid')['revised_cost_cr'].diff().fillna(0)
    
    # For progress delta: first observation has no prior month, so delta is NaN
    delta_prog = df.groupby('project_uid')['physical_progress_pct'].diff()
    df['delta_progress_pct'] = delta_prog.fillna(0)
    
    # Progress stagnation: consecutive months with < 0.5% progress change
    # Note: first month of a project is not stagnant (requires observing across consecutive months)
    is_stagnant = (delta_prog.abs() < 0.5).fillna(False).astype(int)
    df['is_stagnant'] = is_stagnant
    
    # True consecutive streak that increments on stagnant months and resets to 0 when progress resumes
    df['progress_stagnation_streak'] = df.groupby('project_uid')['is_stagnant'].transform(
        lambda s: _calc_streak_array(s.values)
    )
    
    # Cost revision count (cumulative)
    df['is_cost_revised'] = (df['delta_cost_cr'].abs() > 0).astype(int)
    df['cost_revision_count'] = df.groupby('project_uid')['is_cost_revised'].cumsum()
    
    return df


def split_master_and_panel(df: pd.DataFrame):
    """Split into static entity table and time-series fact table."""
    logger.info("Splitting into project_master and project_month_panel...")
    
    # 1. Project Master (static attributes)
    # Take the most recent non-null value for static attributes
    master_cols = [
        'project_code', 'project_name', 'implementing_agency',
        'ministry', 'sector', 'state', 'original_cost_cr', 'approval_date', 
        'start_date', 'original_completion_date'
    ]
    
    # Map sector from ministry if missing or unknown
    if 'sector' not in df.columns or df['sector'].isin(['Unknown', '', None]).all():
        df['sector'] = df['ministry'].apply(derive_sector_from_ministry)
    else:
        mask = df['sector'].isna() | (df['sector'] == 'Unknown') | (df['sector'] == '')
        if mask.any():
            df.loc[mask, 'sector'] = df.loc[mask, 'ministry'].apply(derive_sector_from_ministry)
        
    # Group by uid and take last valid observation
    project_master = df.groupby('project_uid')[master_cols].last().reset_index()
    
    # Compute first/last seen
    seen_dates = df.groupby('project_uid')['report_month'].agg(['min', 'max']).reset_index()
    seen_dates.columns = ['project_uid', 'first_seen_report_month', 'last_seen_report_month']
    
    project_master = project_master.merge(seen_dates, on='project_uid')
    
    # 2. Project Month Panel (time-series)
    panel_cols = [
        'project_uid', 'report_month', 'revised_cost_cr', 'expenditure_cr',
        'physical_progress_pct', 'delta_cost_cr', 'delta_progress_pct',
        'progress_stagnation_streak', 'cost_revision_count',
        'schedule_delay_months', 'is_imputed_cost', 'is_imputed_progress', 'outlier_flag'
    ]
    
    project_month_panel = df[panel_cols].copy()
    
    # Convert dates back to strings for parquet serialization if needed
    project_month_panel['report_month'] = project_month_panel['report_month'].dt.strftime('%Y-%m-%d')
    project_master['first_seen_report_month'] = project_master['first_seen_report_month'].dt.strftime('%Y-%m-%d')
    project_master['last_seen_report_month'] = project_master['last_seen_report_month'].dt.strftime('%Y-%m-%d')
    
    return project_master, project_month_panel


def main():
    input_path = INTERIM_DIR / "merged_long.parquet"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
        
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path.name}")
    
    # Deduplicate intra-month duplicates (Phase 2.2 of Roadmap)
    # Keep the row with highest field-completeness per (project_uid, report_month)
    df['_completeness'] = df.notna().sum(axis=1)
    dups_mask = df.duplicated(subset=['project_uid', 'report_month'], keep=False)
    if dups_mask.any():
        conflicts = df[dups_mask].sort_values(by=['project_uid', 'report_month'])
        conflicts_path = INTERIM_DIR / "dedup_conflicts.csv"
        conflicts.to_csv(conflicts_path, index=False)
        logger.info(f"Logged {dups_mask.sum()} duplicate candidates to {conflicts_path.name}")
        
    df = df.sort_values(by=['project_uid', 'report_month', '_completeness'], ascending=[True, True, False])
    df = df.drop_duplicates(subset=['project_uid', 'report_month'], keep='first').drop(columns=['_completeness'])
    logger.info(f"After deduplication: {len(df)} clean (project, month) observations")
    
    # Preprocessing pipeline
    df = compute_schedule_delay(df)
    df = apply_locf_imputation(df)
    df = flag_outliers(df)
    df = create_panel_features(df)
    
    master_df, panel_df = split_master_and_panel(df)
    
    # Save outputs
    master_path = MASTER_DIR / "project_master.parquet"
    panel_path = MASTER_DIR / "project_month_panel.parquet"
    
    master_df.to_parquet(master_path, index=False)
    panel_df.to_parquet(panel_path, index=False)
    
    logger.info(f"Saved project_master: {len(master_df)} rows")
    logger.info(f"Saved project_month_panel: {len(panel_df)} rows")
    logger.info("Data preprocessing complete!")


if __name__ == "__main__":
    main()
