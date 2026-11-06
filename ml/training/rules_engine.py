"""
SIH 2026 — PS26103 | Phase 7: Early Warning Rules Engine
=========================================================
Implements deterministic, auditable rules that complement ML models.
Detects extreme stagnation, cost spikes, and budget exhaustion risks.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict


def evaluate_project_rules(row: pd.Series) -> Dict[str, any]:
    """
    Evaluates rule-based triggers for a single project observation.
    Returns:
        dict with:
            rule_score: float (0 to 100)
            rule_triggered: bool
            rule_reasons: list of str
            rule_reason_text: str (joined human-readable explanation)
    """
    score = 0.0
    reasons: List[str] = []
    
    revised_cost = float(row.get('revised_cost_cr', 0.0) or 0.0)
    original_cost = float(row.get('original_cost_cr', 0.0) or 0.0)
    expenditure = float(row.get('expenditure_cr', 0.0) or 0.0)
    progress = float(row.get('physical_progress_pct', 0.0) or 0.0)
    stagnation_streak = int(row.get('progress_stagnation_streak', 0) or 0)
    cost_revisions = int(row.get('cost_revision_count', 0) or 0)
    schedule_delay = float(row.get('schedule_delay_months', 0.0) or 0.0)
    
    # Rule 1: Cost Tripled (Cost revision > 300% of original sanction)
    if original_cost > 0 and revised_cost >= 3.0 * original_cost:
        score += 35.0
        reasons.append(f"Sanctioned cost has escalated {revised_cost / original_cost:.1f}x from original ₹{original_cost:.1f} Cr to ₹{revised_cost:.1f} Cr")
        
    # Rule 2: Prolonged Stagnation (>= 6 consecutive months without progress)
    if stagnation_streak >= 6:
        score += 30.0
        reasons.append(f"Work stagnated for {stagnation_streak} consecutive months with near-zero progress")
    elif stagnation_streak >= 3:
        score += 15.0
        reasons.append(f"Work stagnated for {stagnation_streak} consecutive months")
        
    # Rule 3: Premature Budget Depletion (Expenditure > 90% while Progress < 75%)
    if revised_cost > 0 and expenditure >= 0.90 * revised_cost and progress < 75.0:
        score += 25.0
        reasons.append(f"Expenditure at {expenditure / revised_cost * 100:.1f}% of budget while physical progress is only {progress:.1f}%")
        
    # Rule 4: Multiple Revisions with Near-Zero Physical Progress
    if progress < 5.0 and cost_revisions >= 2:
        score += 20.0
        reasons.append(f"Cost revised {cost_revisions} times with under 5% physical progress completed")
        
    # Rule 5: Severe Timeline Slippage (Schedule delay >= 36 months)
    if schedule_delay >= 36.0:
        score += 20.0
        reasons.append(f"Project delayed by {int(schedule_delay)} months beyond original target completion date")

    capped_score = min(100.0, score)
    triggered = len(reasons) > 0 and capped_score >= 25.0
    reason_text = "; ".join(reasons) if reasons else "No deterministic rule violations triggered."
    
    return {
        "rule_score": round(capped_score, 1),
        "rule_triggered": triggered,
        "rule_reasons": reasons,
        "rule_reason_text": reason_text
    }


def apply_rules_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies rule evaluation across all projects in the DataFrame.
    Appends:
        rule_score: float
        rule_triggered: bool
        rule_reason: str
    """
    results = [evaluate_project_rules(row) for _, row in df.iterrows()]
    
    df['rule_score'] = [r['rule_score'] for r in results]
    df['rule_triggered'] = [r['rule_triggered'] for r in results]
    df['rule_reason'] = [r['rule_reason_text'] for r in results]
    
    return df

