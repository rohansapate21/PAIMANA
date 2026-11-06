"""
SIH 2026 — PS26103 | Phase 4 & 5: Feature & Target Engineering
==============================================================
Creates the ML-ready feature matrix from the master datasets.
Implements the critical leakage-free forecasting setup:
Features at time (t) predict the outcome at future time (t + 3 months).

Targets created (Horizon = 3 Months):
- target_cost_overrun_class: 0 (<=5%), 1 (5-25%), 2 (>25%)
- target_delay_class: 0 (<1 mo), 1 (1-12 mos), 2 (>12 mos)

Features included:
- Point-in-time ratios: expenditure_pct, cost_overrun_pct_current
- Multi-step temporal lags: cost_lag_1..3, progress_lag_1..3, schedule_delay_lag_1
- Momentum: ewma_progress, rolling_3m_progress_delta, rolling_3m_cost_growth
- Progress benchmarks: expected_progress_pct, progress_deficit
- Project status: progress_stagnation_streak, cost_revision_count, schedule_delay_months
- Categoricals: ministry, sector, state

Usage:
    python ml/features/build_features.py
"""

from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MASTER_DIR = PROJECT_ROOT / "data" / "master"
FEATURES_DIR = PROJECT_ROOT / "ml" / "features"

FEATURES_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()
import sys
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")


def generate_targets(panel: pd.DataFrame, horizon: int = 3) -> pd.DataFrame:
    """
    Creates leakage-free target variables based on the state at T + horizon months.
    For each (project_uid, report_month = T), target represents the change
    observed at T + 3 months.
    """
    logger.info(f"Generating leakage-free target variables with horizon = {horizon} months...")
    
    panel_sorted = panel.sort_values(['project_uid', 'report_month']).copy()
    
    # 1. Future state at T + horizon months
    future_cost = panel_sorted.groupby('project_uid')['revised_cost_cr'].shift(-horizon)
    future_delay = panel_sorted.groupby('project_uid')['schedule_delay_months'].shift(-horizon)
    has_future = future_cost.notna()
    
    # 2. Cost Overrun Target (% cost growth over the next 3 months)
    cost_growth_3m = np.where(
        panel_sorted['revised_cost_cr'] > 0,
        (future_cost - panel_sorted['revised_cost_cr']) / panel_sorted['revised_cost_cr'],
        0.0
    )
    
    conditions_cost = [
        (cost_growth_3m <= 0.05),
        (cost_growth_3m > 0.05) & (cost_growth_3m <= 0.25),
        (cost_growth_3m > 0.25)
    ]
    cost_classes = np.select(conditions_cost, [0, 1, 2], default=0)
    
    # 3. Schedule Delay Target (delay state at T + 3 months)
    conditions_delay = [
        (future_delay < 1.0),
        (future_delay >= 1.0) & (future_delay <= 12.0),
        (future_delay > 12.0)
    ]
    delay_classes = np.select(conditions_delay, [0, 1, 2], default=0)
    
    # Assign targets (set to NaN for rows without a future observation)
    targets = pd.DataFrame({
        'project_uid': panel_sorted['project_uid'],
        'report_month': panel_sorted['report_month'],
        'cost_growth_3m_pct': np.where(has_future, cost_growth_3m, np.nan),
        'target_cost_overrun_class': np.where(has_future, cost_classes, np.nan),
        'future_schedule_delay_months': future_delay,
        'target_delay_class': np.where(has_future, delay_classes, np.nan)
    })
    
    valid_targets = targets['target_cost_overrun_class'].notna()
    logger.info(f"Rows with observable {horizon}-month future outcomes: {valid_targets.sum()} / {len(targets)}")
    logger.info(f"Cost Overrun Class Distribution:\n{targets.loc[valid_targets, 'target_cost_overrun_class'].value_counts().sort_index()}")
    logger.info(f"Delay Risk Class Distribution:\n{targets.loc[valid_targets, 'target_delay_class'].value_counts().sort_index()}")
    
    return targets


def build_features(panel: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    """
    Creates the feature matrix for each (project, month) observation.
    Includes present ratios, rolling statistics, planned duration deficits, and temporal lags.
    """
    logger.info("Building feature matrix (ratios, lag features, progress deficit, momentum)...")
    
    # Merge panel with static master data
    static_cols = [
        'project_uid', 'ministry', 'sector', 'state', 'original_cost_cr',
        'approval_date', 'original_completion_date'
    ]
    df = panel.merge(master[static_cols], on='project_uid', how='left')
    df['report_month_dt'] = pd.to_datetime(df['report_month'])
    df = df.sort_values(['project_uid', 'report_month_dt'])
    
    # --- Ratio Features ---
    # Expenditure vs Revised Cost
    df['expenditure_pct'] = np.where(
        df['revised_cost_cr'] > 0, 
        df['expenditure_cr'] / df['revised_cost_cr'], 
        0.0
    )
    
    # Current Cost Escalation Ratio from original sanction
    df['cost_overrun_pct_current'] = np.where(
        df['original_cost_cr'] > 0,
        (df['revised_cost_cr'] - df['original_cost_cr']) / df['original_cost_cr'],
        0.0
    ).clip(min=0.0)
    
    # --- Expected Progress & Deficit ---
    approval_dt = pd.to_datetime(df['approval_date'], format='%m/%Y', errors='coerce')
    doc_dt = pd.to_datetime(df['original_completion_date'], format='%m/%Y', errors='coerce')
    report_dt = df['report_month_dt']
    
    planned_duration = (doc_dt.dt.year * 12 + doc_dt.dt.month) - (approval_dt.dt.year * 12 + approval_dt.dt.month)
    planned_duration = planned_duration.clip(lower=1.0).fillna(1.0)
    
    months_since_sanction = (report_dt.dt.year * 12 + report_dt.dt.month) - (approval_dt.dt.year * 12 + approval_dt.dt.month)
    months_since_sanction = months_since_sanction.clip(lower=0.0).fillna(0.0)
    
    df['expected_progress_pct'] = np.clip((months_since_sanction / planned_duration) * 100.0, 0.0, 100.0)
    df['progress_deficit'] = (df['expected_progress_pct'] - df['physical_progress_pct']).clip(lower=0.0)
    
    # --- Rolling / Window Features ---
    df['rolling_3m_progress_delta'] = df.groupby('project_uid')['delta_progress_pct'].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    df['rolling_3m_cost_growth'] = df.groupby('project_uid')['delta_cost_cr'].transform(
        lambda x: x.rolling(window=3, min_periods=1).sum()
    )
    
    # --- Multi-Step Lag Features (Task 1.9) ---
    for lag in [1, 2, 3]:
        df[f'cost_lag_{lag}'] = df.groupby('project_uid')['revised_cost_cr'].shift(lag).fillna(0.0)
        df[f'progress_lag_{lag}'] = df.groupby('project_uid')['physical_progress_pct'].shift(lag).fillna(0.0)
        
    df['schedule_delay_lag_1'] = df.groupby('project_uid')['schedule_delay_months'].shift(1).fillna(0.0)
    
    # Exponentially weighted moving average of physical progress
    df['ewma_progress'] = df.groupby('project_uid')['physical_progress_pct'].transform(
        lambda x: x.ewm(span=3).mean()
    ).fillna(0.0)
    
    df.drop(columns=['report_month_dt'], inplace=True, errors='ignore')
    df.fillna(0, inplace=True)
    return df


def main():
    master_path = MASTER_DIR / "project_master.parquet"
    panel_path = MASTER_DIR / "project_month_panel.parquet"
    
    master = pd.read_parquet(master_path)
    panel = pd.read_parquet(panel_path)
    
    # 1. Create Target Variables with 3-Month Forecasting Horizon
    targets = generate_targets(panel, horizon=3)
    
    # 2. Create Features (Present State with multi-step lags)
    features = build_features(panel, master)
    
    # 3. Merge Features with Targets by (project_uid, report_month)
    feature_matrix = features.merge(targets, on=['project_uid', 'report_month'], how='left')
    
    output_path = FEATURES_DIR / "feature_matrix.parquet"
    feature_matrix.to_parquet(output_path, index=False)
    
    logger.info(f"Saved feature matrix to {output_path} ({len(feature_matrix)} total observations)")
    logger.info("Feature & Target engineering complete!")


if __name__ == "__main__":
    main()
