"""
SIH 2026 — PS26103 | Risk Scoring Service Layer
===============================================
Encapsulates database queries for project risk assessment, portfolio analytics,
risk score history, and SHAP explainability.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc, case
from loguru import logger

from backend.app.models.project import (
    ProjectMaster,
    ProjectMonthPanel,
    RiskScore,
    Explanation,
    Alert
)


def get_latest_report_month(db: Session) -> Optional[str]:
    """Retrieve the most recent report_month present in risk_scores."""
    stmt = select(RiskScore.report_month).order_by(desc(RiskScore.report_month)).limit(1)
    result = db.execute(stmt).scalar_one_or_none()
    return result


def get_dashboard_summary(db: Session) -> Dict[str, Any]:
    """
    Computes portfolio-level executive KPIs:
    - Total projects & active scored projects
    - Risk band distributions (High, Medium, Low)
    - Total original sanctioned cost vs current revised cost
    - Average delay and severe delay project count
    - Active unacknowledged alerts
    """
    latest_month = get_latest_report_month(db)
    total_projects = db.execute(select(func.count(ProjectMaster.project_uid))).scalar() or 0

    if not latest_month:
        return {
            "latest_report_month": None,
            "total_projects": total_projects,
            "active_scored_projects": 0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0,
            "rule_triggered_count": 0,
            "active_alerts_count": 0,
            "total_original_cost_cr": 0.0,
            "total_revised_cost_cr": 0.0,
            "total_expenditure_cr": 0.0,
            "cost_overrun_pct": 0.0,
            "avg_schedule_delay_months": 0.0,
            "risk_distribution": {"High": 0, "Medium": 0, "Low": 0}
        }

    # Risk band distribution for the latest month
    band_counts_stmt = (
        select(RiskScore.risk_band, func.count(RiskScore.id))
        .where(RiskScore.report_month == latest_month)
        .group_by(RiskScore.risk_band)
    )
    band_results = dict(db.execute(band_counts_stmt).all())
    high_count = band_results.get("High", 0)
    med_count = band_results.get("Medium", 0)
    low_count = band_results.get("Low", 0)
    active_scored = high_count + med_count + low_count

    # Rule triggered count
    rule_triggered_stmt = (
        select(func.count(RiskScore.id))
        .where(and_(RiskScore.report_month == latest_month, RiskScore.rule_triggered.is_(True)))
    )
    rule_triggered_count = db.execute(rule_triggered_stmt).scalar() or 0

    # Active alerts count
    active_alerts_stmt = select(func.count(Alert.id)).where(Alert.acknowledged.is_(False))
    active_alerts_count = db.execute(active_alerts_stmt).scalar() or 0

    # Cost and delay aggregates from latest panel
    panel_stats_stmt = (
        select(
            func.sum(ProjectMaster.original_cost_cr).label("orig_cost"),
            func.sum(ProjectMonthPanel.revised_cost_cr).label("rev_cost"),
            func.sum(ProjectMonthPanel.expenditure_cr).label("exp_cost"),
            func.avg(ProjectMonthPanel.schedule_delay_months).label("avg_delay")
        )
        .join(ProjectMonthPanel, ProjectMaster.project_uid == ProjectMonthPanel.project_uid)
        .where(ProjectMonthPanel.report_month == latest_month)
    )
    stats_row = db.execute(panel_stats_stmt).one_or_none()
    
    orig_cost = float(stats_row.orig_cost or 0.0) if stats_row else 0.0
    rev_cost = float(stats_row.rev_cost or 0.0) if stats_row else 0.0
    exp_cost = float(stats_row.exp_cost or 0.0) if stats_row else 0.0
    avg_delay = float(stats_row.avg_delay or 0.0) if stats_row else 0.0

    cost_overrun_pct = round(((rev_cost - orig_cost) / orig_cost * 100.0), 2) if orig_cost > 0 else 0.0

    return {
        "latest_report_month": latest_month,
        "total_projects": total_projects,
        "active_scored_projects": active_scored,
        "high_risk_count": high_count,
        "medium_risk_count": med_count,
        "low_risk_count": low_count,
        "rule_triggered_count": rule_triggered_count,
        "active_alerts_count": active_alerts_count,
        "total_original_cost_cr": round(orig_cost, 2),
        "total_revised_cost_cr": round(rev_cost, 2),
        "total_expenditure_cr": round(exp_cost, 2),
        "cost_overrun_pct": cost_overrun_pct,
        "avg_schedule_delay_months": round(avg_delay, 1),
        "risk_distribution": {
            "High": high_count,
            "Medium": med_count,
            "Low": low_count
        }
    }


def get_projects_with_risk(
    db: Session,
    ministry: Optional[str] = None,
    sector: Optional[str] = None,
    state: Optional[str] = None,
    risk_band: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "risk_score",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Retrieves filtered, sorted and paginated projects joined with latest risk scores and panel data.
    """
    latest_month = get_latest_report_month(db)
    if not latest_month:
        return {"items": [], "total": 0, "limit": limit, "offset": offset}

    # Base query joining ProjectMaster, RiskScore and latest ProjectMonthPanel
    stmt = (
        select(
            ProjectMaster.project_uid,
            ProjectMaster.project_name,
            ProjectMaster.ministry,
            ProjectMaster.sector,
            ProjectMaster.state,
            ProjectMaster.original_cost_cr,
            ProjectMonthPanel.revised_cost_cr,
            ProjectMonthPanel.expenditure_cr,
            ProjectMonthPanel.physical_progress_pct,
            ProjectMonthPanel.schedule_delay_months,
            ProjectMonthPanel.progress_stagnation_streak,
            RiskScore.risk_score,
            RiskScore.risk_band,
            RiskScore.ml_risk_score,
            RiskScore.rule_score,
            RiskScore.rule_triggered,
            RiskScore.shap_explanation
        )
        .outerjoin(
            RiskScore,
            and_(
                ProjectMaster.project_uid == RiskScore.project_uid,
                RiskScore.report_month == latest_month
            )
        )
        .outerjoin(
            ProjectMonthPanel,
            and_(
                ProjectMaster.project_uid == ProjectMonthPanel.project_uid,
                ProjectMonthPanel.report_month == latest_month
            )
        )
    )

    # Filters
    filters = []
    if ministry:
        filters.append(func.lower(ProjectMaster.ministry) == ministry.strip().lower())
    if sector:
        filters.append(func.lower(ProjectMaster.sector) == sector.strip().lower())
    if state:
        filters.append(func.lower(ProjectMaster.state) == state.strip().lower())
    if risk_band:
        filters.append(RiskScore.risk_band == risk_band)
    if search:
        search_pattern = f"%{search.strip().lower()}%"
        filters.append(
            or_(
                func.lower(ProjectMaster.project_name).like(search_pattern),
                func.lower(ProjectMaster.project_uid).like(search_pattern),
                func.lower(ProjectMaster.implementing_agency).like(search_pattern)
            )
        )

    if filters:
        stmt = stmt.where(and_(*filters))

    # Total count calculation
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.execute(count_stmt).scalar() or 0

    # Sorting
    sort_column_map = {
        "risk_score": RiskScore.risk_score,
        "project_name": ProjectMaster.project_name,
        "revised_cost_cr": ProjectMonthPanel.revised_cost_cr,
        "physical_progress_pct": ProjectMonthPanel.physical_progress_pct,
        "schedule_delay_months": ProjectMonthPanel.schedule_delay_months
    }
    col = sort_column_map.get(sort_by, RiskScore.risk_score)
    
    if sort_order.lower() == "asc":
        stmt = stmt.order_by(col.asc().nullslast())
    else:
        stmt = stmt.order_by(col.desc().nullslast())

    # Pagination
    stmt = stmt.limit(limit).offset(offset)
    rows = db.execute(stmt).all()

    items = []
    for r in rows:
        items.append({
            "project_uid": r.project_uid,
            "project_name": r.project_name,
            "ministry": r.ministry,
            "sector": r.sector,
            "state": r.state,
            "original_cost_cr": r.original_cost_cr,
            "revised_cost_cr": r.revised_cost_cr,
            "expenditure_cr": r.expenditure_cr,
            "physical_progress_pct": r.physical_progress_pct,
            "schedule_delay_months": r.schedule_delay_months,
            "progress_stagnation_streak": int(r.progress_stagnation_streak or 0),
            "risk_score": r.risk_score if r.risk_score is not None else 0.0,
            "risk_band": r.risk_band or "Unscored",
            "ml_risk_score": r.ml_risk_score,
            "rule_score": r.rule_score,
            "rule_triggered": bool(r.rule_triggered),
            "shap_explanation": r.shap_explanation or ""
        })

    return {
        "items": items,
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "report_month": latest_month
    }


def get_project_risk(db: Session, project_uid: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves full 360-degree risk assessment for a specific project.
    Includes project metadata, latest risk score, breakdown probabilities,
    SHAP explanation, active alerts, and latest progress metrics.
    """
    latest_month = get_latest_report_month(db)
    
    # 1. Project Master
    master = db.execute(
        select(ProjectMaster).where(ProjectMaster.project_uid == project_uid)
    ).scalar_one_or_none()

    if not master:
        return None

    # 2. Latest Risk Score
    score = db.execute(
        select(RiskScore)
        .where(
            and_(
                RiskScore.project_uid == project_uid,
                RiskScore.report_month == latest_month
            )
        )
    ).scalar_one_or_none()

    # 3. Latest Month Panel
    panel = db.execute(
        select(ProjectMonthPanel)
        .where(
            and_(
                ProjectMonthPanel.project_uid == project_uid,
                ProjectMonthPanel.report_month == latest_month
            )
        )
    ).scalar_one_or_none()

    # 4. Top Explanations
    explanations = []
    if score:
        exp_rows = db.execute(
            select(Explanation)
            .where(Explanation.risk_score_id == score.id)
            .order_by(desc(Explanation.shap_value))
            .limit(5)
        ).scalars().all()
        explanations = [
            {
                "feature_name": e.feature_name,
                "shap_value": e.shap_value,
                "explanation_text": e.explanation_text
            }
            for e in exp_rows
        ]

    # 5. Recent Alerts
    alert_rows = db.execute(
        select(Alert)
        .where(Alert.project_uid == project_uid)
        .order_by(desc(Alert.created_at))
        .limit(5)
    ).scalars().all()
    alerts = [
        {
            "id": a.id,
            "project_uid": a.project_uid,
            "report_month": a.report_month,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "reason": a.reason,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "acknowledged": a.acknowledged
        }
        for a in alert_rows
    ]

    return {
        "project_uid": master.project_uid,
        "project_name": master.project_name,
        "ministry": master.ministry,
        "sector": master.sector,
        "state": master.state,
        "implementing_agency": master.implementing_agency,
        "original_cost_cr": master.original_cost_cr,
        "approval_date": master.approval_date,
        "start_date": master.start_date,
        "original_completion_date": master.original_completion_date,
        "latest_metrics": {
            "report_month": panel.report_month if panel else latest_month,
            "revised_cost_cr": panel.revised_cost_cr if panel else master.original_cost_cr,
            "expenditure_cr": panel.expenditure_cr if panel else 0.0,
            "physical_progress_pct": panel.physical_progress_pct if panel else 0.0,
            "schedule_delay_months": panel.schedule_delay_months if panel else 0.0,
            "progress_stagnation_streak": panel.progress_stagnation_streak if panel else 0,
            "cost_revision_count": panel.cost_revision_count if panel else 0,
            "outlier_flag": panel.outlier_flag if panel else False
        },
        "risk_assessment": {
            "risk_score": score.risk_score if score else None,
            "risk_band": score.risk_band if score else "Unscored",
            "ml_risk_score": score.ml_risk_score if score else None,
            "rule_score": score.rule_score if score else None,
            "rule_triggered": score.rule_triggered if score else False,
            "cost_risk_prob": score.cost_risk_prob if score else None,
            "delay_risk_prob": score.delay_risk_prob if score else None,
            "shap_explanation": score.shap_explanation if score else None,
            "model_version": score.model_version if score else "v1.0"
        },
        "explanations": explanations,
        "alerts": alerts
    }


def get_risk_history(db: Session, project_uid: str) -> List[Dict[str, Any]]:
    """
    Returns the longitudinal timeline for a project, joining risk scores
    with panel metrics chronologically.
    """
    stmt = (
        select(
            ProjectMonthPanel.report_month,
            ProjectMonthPanel.revised_cost_cr,
            ProjectMonthPanel.expenditure_cr,
            ProjectMonthPanel.physical_progress_pct,
            ProjectMonthPanel.schedule_delay_months,
            ProjectMonthPanel.progress_stagnation_streak,
            RiskScore.risk_score,
            RiskScore.risk_band,
            RiskScore.rule_triggered
        )
        .outerjoin(
            RiskScore,
            and_(
                ProjectMonthPanel.project_uid == RiskScore.project_uid,
                ProjectMonthPanel.report_month == RiskScore.report_month
            )
        )
        .where(ProjectMonthPanel.project_uid == project_uid)
        .order_by(ProjectMonthPanel.report_month.asc())
    )

    rows = db.execute(stmt).all()
    history = []
    for r in rows:
        history.append({
            "report_month": r.report_month,
            "revised_cost_cr": r.revised_cost_cr,
            "expenditure_cr": r.expenditure_cr,
            "physical_progress_pct": r.physical_progress_pct,
            "schedule_delay_months": r.schedule_delay_months,
            "progress_stagnation_streak": r.progress_stagnation_streak,
            "risk_score": r.risk_score,
            "risk_band": r.risk_band,
            "rule_triggered": bool(r.rule_triggered) if r.rule_triggered is not None else False
        })
    return history


def get_ministry_breakdown(db: Session) -> List[Dict[str, Any]]:
    """
    Aggregates project counts and risk profiles by ministry for the latest month.
    """
    latest_month = get_latest_report_month(db)
    if not latest_month:
        return []

    stmt = (
        select(
            ProjectMaster.ministry,
            func.count(ProjectMaster.project_uid).label("total_projects"),
            func.count(RiskScore.id).label("scored_projects"),
            func.sum(
                case((RiskScore.risk_band == "High", 1), else_=0)
            ).label("high_risk_count"),
            func.sum(
                case((RiskScore.risk_band == "Medium", 1), else_=0)
            ).label("med_risk_count"),
            func.sum(
                case((RiskScore.risk_band == "Low", 1), else_=0)
            ).label("low_risk_count"),
            func.avg(RiskScore.risk_score).label("avg_risk_score"),
            func.sum(ProjectMaster.original_cost_cr).label("total_original_cost"),
            func.sum(ProjectMonthPanel.revised_cost_cr).label("total_revised_cost")
        )
        .outerjoin(
            RiskScore,
            and_(
                ProjectMaster.project_uid == RiskScore.project_uid,
                RiskScore.report_month == latest_month
            )
        )
        .outerjoin(
            ProjectMonthPanel,
            and_(
                ProjectMaster.project_uid == ProjectMonthPanel.project_uid,
                ProjectMonthPanel.report_month == latest_month
            )
        )
        .group_by(ProjectMaster.ministry)
        .order_by(desc("high_risk_count"), desc("avg_risk_score"))
    )

    rows = db.execute(stmt).all()
    results = []
    for r in rows:
        results.append({
            "ministry": r.ministry,
            "total_projects": r.total_projects,
            "scored_projects": r.scored_projects,
            "high_risk_count": int(r.high_risk_count or 0),
            "med_risk_count": int(r.med_risk_count or 0),
            "low_risk_count": int(r.low_risk_count or 0),
            "avg_risk_score": round(float(r.avg_risk_score or 0.0), 1),
            "total_original_cost_cr": round(float(r.total_original_cost or 0.0), 2),
            "total_revised_cost_cr": round(float(r.total_revised_cost or 0.0), 2)
        })
    return results


def get_risk_trend(db: Session) -> List[Dict[str, Any]]:
    """
    Returns longitudinal month-over-month trend of risk band counts.
    """
    stmt = (
        select(
            RiskScore.report_month,
            RiskScore.risk_band,
            func.count(RiskScore.id).label("count")
        )
        .group_by(RiskScore.report_month, RiskScore.risk_band)
        .order_by(RiskScore.report_month.asc())
    )

    rows = db.execute(stmt).all()
    months_map: Dict[str, Dict[str, int]] = {}
    for r in rows:
        if r.report_month not in months_map:
            months_map[r.report_month] = {"High": 0, "Medium": 0, "Low": 0}
        months_map[r.report_month][r.risk_band] = r.count

    return [
        {
            "report_month": month,
            "High": bands.get("High", 0),
            "Medium": bands.get("Medium", 0),
            "Low": bands.get("Low", 0)
        }
        for month, bands in sorted(months_map.items())
    ]


def get_state_breakdown(db: Session) -> List[Dict[str, Any]]:
    """
    Aggregates project counts and risk profiles by State for the latest reporting month.
    """
    latest_month = get_latest_report_month(db)
    if not latest_month:
        return []

    stmt = (
        select(
            ProjectMaster.state,
            func.count(ProjectMaster.project_uid).label("total_projects"),
            func.count(RiskScore.id).label("scored_projects"),
            func.sum(
                case((RiskScore.risk_band == "High", 1), else_=0)
            ).label("high_risk_count"),
            func.sum(
                case((RiskScore.risk_band == "Medium", 1), else_=0)
            ).label("med_risk_count"),
            func.sum(
                case((RiskScore.risk_band == "Low", 1), else_=0)
            ).label("low_risk_count"),
            func.avg(RiskScore.risk_score).label("avg_risk_score"),
            func.sum(ProjectMaster.original_cost_cr).label("total_original_cost")
        )
        .outerjoin(
            RiskScore,
            and_(
                ProjectMaster.project_uid == RiskScore.project_uid,
                RiskScore.report_month == latest_month
            )
        )
        .where(and_(ProjectMaster.state.is_not(None), ProjectMaster.state != "Unknown"))
        .group_by(ProjectMaster.state)
        .order_by(desc("total_projects"))
    )

    rows = db.execute(stmt).all()
    results = []
    for r in rows:
        results.append({
            "state": r.state,
            "total_projects": r.total_projects,
            "scored_projects": r.scored_projects,
            "high_risk_count": int(r.high_risk_count or 0),
            "med_risk_count": int(r.med_risk_count or 0),
            "low_risk_count": int(r.low_risk_count or 0),
            "avg_risk_score": round(float(r.avg_risk_score or 0.0), 1),
            "total_original_cost_cr": round(float(r.total_original_cost or 0.0), 2)
        })
    return results
