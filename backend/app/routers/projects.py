"""
SIH 2026 — PS26103 | Projects & Risk Analytics Router
=====================================================
Database-backed router providing project discovery, multi-criteria filtering,
360-degree risk profiles, SHAP driver explanations, and historical trends.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.deps import get_current_user_optional
from backend.app.models.project import User
from backend.app.schemas.project import (
    ProjectListResponse,
    ProjectRiskResponse,
    ProjectHistoryItem
)
from backend.app.services.risk_scoring import (
    get_projects_with_risk,
    get_project_risk,
    get_risk_history
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse)
def list_projects(
    ministry: Optional[str] = Query(None, description="Filter by ministry name"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    state: Optional[str] = Query(None, description="Filter by state"),
    risk_band: Optional[str] = Query(None, description="Filter by risk band (High, Medium, Low)"),
    search: Optional[str] = Query(None, description="Search across project name, ID, or implementing agency"),
    sort_by: str = Query("risk_score", description="Sort by risk_score, project_name, revised_cost_cr, physical_progress_pct, schedule_delay_months"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Search and filter infrastructure projects with latest composite risk scores,
    physical progress, cost revisions, and delay metrics.
    """
    results = get_projects_with_risk(
        db=db,
        ministry=ministry,
        sector=sector,
        state=state,
        risk_band=risk_band,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    return results


@router.get("/{project_uid}", response_model=ProjectRiskResponse)
def get_project_by_uid(
    project_uid: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Retrieve project master information and latest risk status.
    """
    project = get_project_risk(db=db, project_uid=project_uid)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with UID '{project_uid}' not found."
        )
    return project


@router.get("/{project_uid}/risk", response_model=ProjectRiskResponse)
def get_project_risk_assessment(
    project_uid: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Detailed 360-degree risk assessment including ML probabilities,
    rule violations, top SHAP driver explanations, and active alerts.
    """
    project = get_project_risk(db=db, project_uid=project_uid)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with UID '{project_uid}' not found."
        )
    return project


@router.get("/{project_uid}/history", response_model=List[ProjectHistoryItem])
def get_project_timeline(
    project_uid: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Retrieves the longitudinal historical timeline for a project,
    tracking monthly cost revisions, cumulative expenditure, progress, and risk scores.
    """
    history = get_risk_history(db=db, project_uid=project_uid)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No timeline data found for project '{project_uid}'."
        )
    return history
