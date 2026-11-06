"""
SIH 2026 — PS26103 | Phase 7 & 8: Composite Risk Scoring & Explainability
========================================================================
Loads trained Cost Overrun (XGBoost) and Time Delay (LightGBM) models.
Computes an absolute, multi-factor 0-100 Composite Project Risk Score:
    Score = 0.45 * CostEscalation + 0.35 * ScheduleDelay + 0.10 * Stagnation + 0.10 * CostRevisions
Incorporates deterministic Early Warning rules as a safety floor.
Generates plain-language NLG explanations using SHAP tree attribution and rule audits.

Usage:
    python ml/training/generate_risk_scores.py
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np
import joblib
import shap
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.training.rules_engine import apply_rules_dataframe

FEATURES_DIR = PROJECT_ROOT / "ml" / "features"
MODELS_DIR = PROJECT_ROOT / "ml" / "models"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "eda_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")


def generate_nlg_explanation(
    shap_cost_row: np.ndarray,
    shap_delay_row: np.ndarray,
    feature_names: list,
    row_data: pd.Series
) -> str:
    """
    Converts SHAP feature impact values and rule audit flags into
    an authoritative plain-language explanation for government decision-makers.
    """
    reasons = []
    
    # 1. If deterministic rules fired, include rule justification first
    rule_reason = str(row_data.get('rule_reason', '') or '').strip()
    if row_data.get('rule_triggered', False) and rule_reason and "No deterministic" not in rule_reason:
        reasons.append(rule_reason)
        
    # 2. Extract top risk drivers from ML SHAP values
    combined_impacts = []
    for i, feat in enumerate(feature_names):
        cost_impact = float(shap_cost_row[i]) if i < len(shap_cost_row) else 0.0
        delay_impact = float(shap_delay_row[i]) if i < len(shap_delay_row) else 0.0
        # Positive impact = increased risk
        combined_impact = (0.55 * cost_impact) + (0.45 * delay_impact)
        combined_impacts.append({
            "feature": feat,
            "impact": combined_impact,
            "value": row_data.get(feat, 0)
        })
        
    combined_impacts = sorted(combined_impacts, key=lambda x: x["impact"], reverse=True)
    positive_drivers = [x for x in combined_impacts if x["impact"] > 0][:2]
    
    ml_reasons = []
    for d in positive_drivers:
        feat = d["feature"]
        val = d["value"]
        
        if feat == "schedule_delay_months" and float(val) > 0:
            ml_reasons.append(f"accumulated schedule delay of {int(val)} months")
        elif feat == "expenditure_pct" and float(val) > 0:
            ml_reasons.append(f"budget expenditure ratio tracking at {float(val)*100:.1f}%")
        elif feat == "cost_revision_count" and int(val) > 0:
            ml_reasons.append(f"budget revised {int(val)} times")
        elif feat == "progress_stagnation_streak" and int(val) > 0:
            ml_reasons.append(f"work stagnated for {int(val)} consecutive months")
        elif feat == "rolling_3m_cost_growth" and float(val) > 0:
            ml_reasons.append(f"recent ₹{float(val):.1f} Cr cost jump over last 3 months")
        elif feat == "original_cost_cr" and float(val) > 0:
            ml_reasons.append(f"high project scale (₹{float(val):.1f} Cr sanction)")
        elif feat in ["ministry", "sector", "state"]:
            ml_reasons.append(f"historical risk profile in {feat} '{val}'")
        else:
            ml_reasons.append(f"concerning trajectory in {feat.replace('_', ' ')}")
            
    if ml_reasons:
        reasons.append("ML models indicate: " + " and ".join(ml_reasons))
        
    if not reasons:
        return "Normal project trajectory consistent with baseline infrastructure schedules."
        
    return "; ".join(reasons) + "."


def main():
    cost_model_path = MODELS_DIR / "best_model_cost.joblib"
    delay_model_path = MODELS_DIR / "best_model_delay.joblib"
    features_path = FEATURES_DIR / "feature_matrix.parquet"
    
    if not cost_model_path.exists() or not delay_model_path.exists():
        logger.error("Model artifacts not found. Please train cost and delay models first.")
        return
        
    logger.info("Loading model artifacts and feature matrix...")
    cost_artifact = joblib.load(cost_model_path)
    delay_artifact = joblib.load(delay_model_path)
    
    cost_model = cost_artifact['model']
    delay_model = delay_artifact['model']
    feature_cols = cost_artifact['features']
    category_mappings = cost_artifact.get('category_mappings', {})
    
    df = pd.read_parquet(features_path)
    latest_month = df['report_month'].max()
    logger.info(f"Generating Composite Risk Scores for latest report month: {latest_month}")
    
    current_data = df[df['report_month'] == latest_month].copy()
    
    # Merge project names from master
    master_path = PROJECT_ROOT / "data" / "master" / "project_master.parquet"
    master = pd.read_parquet(master_path)[['project_uid', 'project_name']]
    current_data = current_data.merge(master, on='project_uid', how='left')
    
    # Prepare features for ML prediction with aligned categoricals
    X = current_data[feature_cols].copy()
    for col, categories in category_mappings.items():
        if col in X.columns:
            X[col] = pd.Categorical(X[col], categories=categories)
            
    logger.info(f"Scoring {len(X)} active projects...")
    
    # 1. Predict Model Probabilities
    cost_probs = cost_model.predict_proba(X)   # Classes: [0: Safe, 1: Moderate, 2: Severe]
    delay_probs = delay_model.predict_proba(X) # Classes: [0: No Delay, 1: Minor, 2: Severe]
    
    # Probability of adverse outcome (weighted severity probability)
    cost_severity_prob = (cost_probs[:, 1] * 0.40) + (cost_probs[:, 2] * 1.00)
    delay_severity_prob = (delay_probs[:, 1] * 0.40) + (delay_probs[:, 2] * 1.00)
    
    current_data['cost_risk_prob'] = cost_severity_prob.round(4)
    current_data['delay_risk_prob'] = delay_severity_prob.round(4)
    
    # 2. Compute Velocity & Stagnation Factors
    stagnation_factor = np.clip(current_data['progress_stagnation_streak'] / 6.0, 0.0, 1.0)
    revision_factor = np.clip(current_data['cost_revision_count'] / 5.0, 0.0, 1.0)
    
    # 3. Absolute Multi-Factor ML Risk Score (0 - 100 scale)
    ml_risk_score = (
        0.45 * (cost_severity_prob * 100.0) +
        0.35 * (delay_severity_prob * 100.0) +
        0.10 * (stagnation_factor * 100.0) +
        0.10 * (revision_factor * 100.0)
    )
    current_data['ml_risk_score'] = ml_risk_score.round(1)
    
    # 4. Evaluate Early Warning Rules Engine
    logger.info("Evaluating deterministic early warning rules...")
    current_data = apply_rules_dataframe(current_data)
    
    # 5. Composite Final Risk Score (Rules act as safety floor)
    final_score = np.maximum(current_data['ml_risk_score'], current_data['rule_score'])
    current_data['risk_score'] = np.clip(final_score, 0.0, 100.0).round(1)
    
    # 6. Risk Banding
    conditions = [
        (current_data['risk_score'] <= 40.0),
        (current_data['risk_score'] > 40.0) & (current_data['risk_score'] <= 70.0),
        (current_data['risk_score'] > 70.0)
    ]
    current_data['risk_band'] = np.select(conditions, ['Low', 'Medium', 'High'], default='Low')
    
    logger.info(f"Risk Band Distribution:\n{current_data['risk_band'].value_counts().to_string()}")
    logger.info(f"Rule-Triggered Projects: {current_data['rule_triggered'].sum()}")
    
    # 7. Compute SHAP Attribution for Medium & High Risk Projects
    logger.info("Computing SHAP explanations for elevated risk projects...")
    elevated_mask = current_data['risk_band'].isin(['Medium', 'High'])
    X_elevated = X[elevated_mask]
    
    explanations = []
    if len(X_elevated) > 0:
        explainer_cost = shap.TreeExplainer(cost_model)
        explainer_delay = shap.TreeExplainer(delay_model)
        
        shap_cost = explainer_cost.shap_values(X_elevated)
        shap_delay = explainer_delay.shap_values(X_elevated)
        
        # Severe class SHAP values
        if isinstance(shap_cost, list):
            target_shap_cost = shap_cost[2]
        elif hasattr(shap_cost, 'shape') and len(shap_cost.shape) == 3:
            target_shap_cost = shap_cost[:, :, 2]
        else:
            target_shap_cost = shap_cost
            
        if isinstance(shap_delay, list):
            target_shap_delay = shap_delay[2]
        elif hasattr(shap_delay, 'shape') and len(shap_delay.shape) == 3:
            target_shap_delay = shap_delay[:, :, 2]
        else:
            target_shap_delay = shap_delay
            
        elevated_indices = current_data[elevated_mask].index
        for idx, row_i in enumerate(elevated_indices):
            row_data = current_data.loc[row_i]
            expl = generate_nlg_explanation(
                target_shap_cost[idx],
                target_shap_delay[idx],
                feature_cols,
                row_data
            )
            explanations.append(expl)
            
        current_data.loc[elevated_mask, 'shap_explanation'] = explanations
    else:
        current_data['shap_explanation'] = "Low risk project within normal operational thresholds."
        
    current_data['shap_explanation'] = current_data['shap_explanation'].fillna("Within normal operational limits.")
    
    # 8. Save Final CSV
    output_cols = [
        'project_uid', 'project_name', 'ministry', 'sector', 'state', 'report_month',
        'risk_score', 'risk_band', 'ml_risk_score', 'rule_score', 'rule_triggered',
        'cost_risk_prob', 'delay_risk_prob', 'shap_explanation'
    ]
    
    results = current_data[output_cols].sort_values('risk_score', ascending=False)
    out_path = OUTPUT_DIR / "latest_risk_scores.csv"
    results.to_csv(out_path, index=False, encoding='utf-8-sig')
    logger.info(f"Saved {len(results)} risk scores to {out_path}")
    
    logger.info("\n--- Top 3 Highest Risk Projects ---")
    for _, row in results.head(3).iterrows():
        logger.info(f"[{row['risk_score']}/100 | {row['risk_band']}] {str(row['project_name'])[:40]}... -> {row['shap_explanation']}")


if __name__ == "__main__":
    main()
