"""
SIH 2026 — PS26103 | Project, Risk & Alerting Pydantic Schemas
==============================================================
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ProjectListItem(BaseModel):
    project_uid: str
    project_name: str
    ministry: str
    sector: str
    state: Optional[str] = None
    original_cost_cr: Optional[float] = None
    revised_cost_cr: Optional[float] = None
    expenditure_cr: Optional[float] = None
    physical_progress_pct: Optional[float] = None
    schedule_delay_months: Optional[float] = None
    progress_stagnation_streak: Optional[int] = 0
    risk_score: float = 0.0
    risk_band: str = "Unscored"
    ml_risk_score: Optional[float] = None
    rule_score: Optional[float] = None
    rule_triggered: bool = False
    shap_explanation: str = ""


class ProjectListResponse(BaseModel):
    items: List[ProjectListItem]
    total: int
    limit: int
    offset: int
    report_month: Optional[str] = None


class ProjectMetrics(BaseModel):
    report_month: Optional[str] = None
    revised_cost_cr: Optional[float] = None
    expenditure_cr: Optional[float] = None
    physical_progress_pct: Optional[float] = None
    schedule_delay_months: Optional[float] = None
    progress_stagnation_streak: int = 0
    cost_revision_count: int = 0
    outlier_flag: bool = False


class ProjectRiskDetail(BaseModel):
    risk_score: Optional[float] = None
    risk_band: str = "Unscored"
    ml_risk_score: Optional[float] = None
    rule_score: Optional[float] = None
    rule_triggered: bool = False
    cost_risk_prob: Optional[float] = None
    delay_risk_prob: Optional[float] = None
    shap_explanation: Optional[str] = None
    model_version: str = "v1.0"


class ExplanationItem(BaseModel):
    feature_name: str
    shap_value: float
    explanation_text: Optional[str] = None


class AlertItem(BaseModel):
    id: int
    project_uid: Optional[str] = None
    project_name: Optional[str] = None
    ministry: Optional[str] = None
    sector: Optional[str] = None
    state: Optional[str] = None
    report_month: Optional[str] = None
    alert_type: str
    severity: str
    reason: str
    created_at: Optional[str] = None
    acknowledged: bool = False


class ProjectRiskResponse(BaseModel):
    project_uid: str
    project_name: str
    ministry: str
    sector: str
    state: Optional[str] = None
    implementing_agency: Optional[str] = None
    original_cost_cr: Optional[float] = None
    approval_date: Optional[str] = None
    start_date: Optional[str] = None
    original_completion_date: Optional[str] = None
    latest_metrics: ProjectMetrics
    risk_assessment: ProjectRiskDetail
    explanations: List[ExplanationItem] = []
    alerts: List[AlertItem] = []


class ProjectHistoryItem(BaseModel):
    report_month: str
    revised_cost_cr: Optional[float] = None
    expenditure_cr: Optional[float] = None
    physical_progress_pct: Optional[float] = None
    schedule_delay_months: Optional[float] = None
    progress_stagnation_streak: int = 0
    risk_score: Optional[float] = None
    risk_band: Optional[str] = None
    rule_triggered: bool = False


class DashboardSummaryResponse(BaseModel):
    latest_report_month: Optional[str] = None
    total_projects: int
    active_scored_projects: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    rule_triggered_count: int
    active_alerts_count: int
    total_original_cost_cr: float
    total_revised_cost_cr: float
    total_expenditure_cr: float
    cost_overrun_pct: float
    avg_schedule_delay_months: float
    risk_distribution: Dict[str, int]


class MinistryBreakdownItem(BaseModel):
    ministry: str
    total_projects: int
    scored_projects: int
    high_risk_count: int
    med_risk_count: int
    low_risk_count: int
    avg_risk_score: float
    total_original_cost_cr: float
    total_revised_cost_cr: float


class RiskTrendItem(BaseModel):
    report_month: str
    High: int
    Medium: int
    Low: int


class AlertListResponse(BaseModel):
    items: List[AlertItem]
    total: int
    limit: int
    offset: int


class AlertAcknowledgeResponse(BaseModel):
    id: int
    project_uid: str
    acknowledged: bool
    acknowledged_at: str
