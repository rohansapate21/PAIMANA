"""
SIH 2026 — PS26103 | Early Warning Alerts Router
================================================
Delivers proactive infrastructure early warnings, severity filtering,
acknowledgment workflows, and alert summary statistics.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.deps import get_current_user, get_current_user_optional
from backend.app.models.project import User
from backend.app.schemas.project import (
    AlertListResponse,
    AlertAcknowledgeResponse
)
from backend.app.services.alerting import (
    get_active_alerts,
    acknowledge_alert,
    generate_alerts_for_month,
    get_alert_summary
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: High, Medium, Low"),
    alert_type: Optional[str] = Query(None, description="Filter by type: rule_triggered, ml_high_risk"),
    ministry: Optional[str] = Query(None, description="Filter by project ministry"),
    acknowledged: Optional[bool] = Query(False, description="Filter by acknowledgment state (default: active/unacknowledged)"),
    limit: int = Query(50, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    List early warning alerts with metadata, severity levels, and SHAP-based explanation rationale.
    """
    alerts = get_active_alerts(
        db=db,
        severity=severity,
        alert_type=alert_type,
        ministry=ministry,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset
    )
    return alerts


@router.get("/summary")
def get_alerts_summary(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get aggregated counts of active alerts grouped by severity and rule trigger type.
    """
    return get_alert_summary(db=db)


@router.patch("/{alert_id}/acknowledge", response_model=AlertAcknowledgeResponse)
def acknowledge_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Acknowledge a pending alert, recording the action.
    """
    result = acknowledge_alert(db=db, alert_id=alert_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found."
        )
    return result


@router.post("/generate")
def trigger_alert_generation(
    report_month: Optional[str] = Query(None, description="Report month (YYYY-MM-DD), defaults to latest"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Evaluate latest project risk scores and generate proactive alert entries (requires authentication).
    """
    created_count = generate_alerts_for_month(db=db, report_month=report_month)
    return {
        "status": "SUCCESS",
        "message": f"Generated {created_count} new alerts for {report_month or 'latest month'}.",
        "new_alerts_count": created_count
    }

