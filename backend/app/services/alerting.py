"""
SIH 2026 — PS26103 | Proactive Alerting Service Layer
=====================================================
Manages early warning notifications, alert generation rules, acknowledgments,
and executive filtering for infrastructure anomalies.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc
from loguru import logger

from backend.app.models.project import ProjectMaster, RiskScore, Alert


def get_active_alerts(
    db: Session,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    ministry: Optional[str] = None,
    acknowledged: Optional[bool] = False,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Fetches alerts with project metadata, supporting multi-criteria filtering
    and pagination.
    """
    stmt = (
        select(
            Alert.id,
            Alert.project_uid,
            ProjectMaster.project_name,
            ProjectMaster.ministry,
            ProjectMaster.sector,
            ProjectMaster.state,
            Alert.report_month,
            Alert.alert_type,
            Alert.severity,
            Alert.reason,
            Alert.created_at,
            Alert.acknowledged
        )
        .join(ProjectMaster, Alert.project_uid == ProjectMaster.project_uid)
    )

    filters = []
    if acknowledged is not None:
        filters.append(Alert.acknowledged == acknowledged)
    if severity:
        filters.append(func.lower(Alert.severity) == severity.strip().lower())
    if alert_type:
        filters.append(Alert.alert_type == alert_type.strip())
    if ministry:
        filters.append(func.lower(ProjectMaster.ministry) == ministry.strip().lower())

    if filters:
        stmt = stmt.where(and_(*filters))

    # Total count calculation
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.execute(count_stmt).scalar() or 0

    # Sort most recent first
    stmt = stmt.order_by(Alert.created_at.desc(), Alert.id.desc()).limit(limit).offset(offset)
    rows = db.execute(stmt).all()

    items = []
    for r in rows:
        items.append({
            "id": r.id,
            "project_uid": r.project_uid,
            "project_name": r.project_name,
            "ministry": r.ministry,
            "sector": r.sector,
            "state": r.state,
            "report_month": r.report_month,
            "alert_type": r.alert_type,
            "severity": r.severity,
            "reason": r.reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "acknowledged": r.acknowledged
        })

    return {
        "items": items,
        "total": total_count,
        "limit": limit,
        "offset": offset
    }


def acknowledge_alert(db: Session, alert_id: int) -> Optional[Dict[str, Any]]:
    """
    Acknowledge a specific alert by ID.
    """
    alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar_one_or_none()
    if not alert:
        return None

    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    logger.info(f"Alert {alert_id} for project {alert.project_uid} acknowledged.")

    return {
        "id": alert.id,
        "project_uid": alert.project_uid,
        "acknowledged": alert.acknowledged,
        "acknowledged_at": datetime.utcnow().isoformat()
    }


def generate_alerts_for_month(db: Session, report_month: Optional[str] = None) -> int:
    """
    Scans risk scores for the target month and generates Alert rows
    for rule-triggered or High-risk projects without duplicating existing alerts.
    """
    if not report_month:
        month_stmt = select(RiskScore.report_month).order_by(desc(RiskScore.report_month)).limit(1)
        report_month = db.execute(month_stmt).scalar_one_or_none()

    if not report_month:
        logger.warning("No scored report months found to generate alerts.")
        return 0

    # Find candidates: High risk band OR rule triggered
    candidates_stmt = (
        select(RiskScore)
        .where(
            and_(
                RiskScore.report_month == report_month,
                or_(
                    RiskScore.risk_band == "High",
                    RiskScore.rule_triggered.is_(True)
                )
            )
        )
    )
    candidates = db.execute(candidates_stmt).scalars().all()

    # Existing alerts for this month
    existing_alerts_stmt = (
        select(Alert.project_uid, Alert.alert_type)
        .where(Alert.report_month == report_month)
    )
    existing_set = set(db.execute(existing_alerts_stmt).all())

    new_alerts = []
    for cand in candidates:
        alert_type = "rule_triggered" if cand.rule_triggered else "ml_high_risk"
        
        # Avoid duplicate alert
        if (cand.project_uid, alert_type) in existing_set:
            continue

        severity = "High" if (cand.risk_score >= 70.0 or (cand.rule_score and cand.rule_score >= 30.0)) else "Medium"
        reason = cand.shap_explanation or f"High risk anomaly detected (Risk Score: {cand.risk_score:.1f})"

        new_alert = Alert(
            project_uid=cand.project_uid,
            report_month=report_month,
            alert_type=alert_type,
            severity=severity,
            reason=reason,
            created_at=datetime.utcnow(),
            acknowledged=False
        )
        new_alerts.append(new_alert)
        existing_set.add((cand.project_uid, alert_type))

    if new_alerts:
        db.add_all(new_alerts)
        db.commit()
        logger.info(f"Generated {len(new_alerts)} new early warning alerts for {report_month}.")

    return len(new_alerts)


def get_alert_summary(db: Session) -> Dict[str, Any]:
    """
    Returns aggregated KPIs of active unacknowledged alerts.
    """
    total_active = db.execute(
        select(func.count(Alert.id)).where(Alert.acknowledged.is_(False))
    ).scalar() or 0

    severity_stmt = (
        select(Alert.severity, func.count(Alert.id))
        .where(Alert.acknowledged.is_(False))
        .group_by(Alert.severity)
    )
    sev_counts = dict(db.execute(severity_stmt).all())

    type_stmt = (
        select(Alert.alert_type, func.count(Alert.id))
        .where(Alert.acknowledged.is_(False))
        .group_by(Alert.alert_type)
    )
    type_counts = dict(db.execute(type_stmt).all())

    return {
        "total_active_alerts": total_active,
        "by_severity": {
            "High": sev_counts.get("High", 0),
            "Medium": sev_counts.get("Medium", 0),
            "Low": sev_counts.get("Low", 0)
        },
        "by_type": type_counts
    }

