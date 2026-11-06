"""
SIH 2026 — PS26103 | Backend Services Module
"""

from backend.app.services.risk_scoring import (
    get_dashboard_summary,
    get_projects_with_risk,
    get_project_risk,
    get_risk_history,
    get_ministry_breakdown,
    get_risk_trend,
    get_state_breakdown
)

from backend.app.services.alerting import (
    get_active_alerts,
    acknowledge_alert,
    generate_alerts_for_month,
    get_alert_summary
)

__all__ = [
    "get_dashboard_summary",
    "get_projects_with_risk",
    "get_project_risk",
    "get_risk_history",
    "get_ministry_breakdown",
    "get_risk_trend",
    "get_active_alerts",
    "acknowledge_alert",
    "generate_alerts_for_month",
    "get_alert_summary",
]

