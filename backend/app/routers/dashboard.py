"""
SIH 2026 — PS26103 | Executive Dashboard Router
===============================================
Serves portfolio-wide KPIs, ministry comparisons, and temporal risk trajectories
with Redis caching for rapid client response times.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.deps import get_current_user_optional
from backend.app.models.project import User
from backend.app.core.cache import get_cache, set_cache
from backend.app.schemas.project import (
    DashboardSummaryResponse,
    MinistryBreakdownItem,
    RiskTrendItem
)
from backend.app.services.risk_scoring import (
    get_dashboard_summary,
    get_ministry_breakdown,
    get_risk_trend,
    get_state_breakdown
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

CACHE_TTL_SUMMARY = 300  # 5 minutes


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Retrieve macro portfolio indicators (counts, cost overruns, delays, risk band proportions).
    Cached via Redis / in-memory store with 5-minute TTL.
    """
    cache_key = "dashboard:summary"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    summary = get_dashboard_summary(db=db)
    await set_cache(cache_key, summary, ttl_seconds=CACHE_TTL_SUMMARY)
    return summary


@router.get("/ministry-breakdown", response_model=List[MinistryBreakdownItem])
async def get_ministries(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Aggregates project counts and risk profiles by ministry for the active reporting period.
    """
    cache_key = "dashboard:ministry_breakdown"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    data = get_ministry_breakdown(db=db)
    await set_cache(cache_key, data, ttl_seconds=CACHE_TTL_SUMMARY)
    return data


@router.get("/risk-trend", response_model=List[RiskTrendItem])
async def get_trend(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Returns month-over-month risk distribution trajectory across historical report periods.
    """
    cache_key = "dashboard:risk_trend"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    data = get_risk_trend(db=db)
    await set_cache(cache_key, data, ttl_seconds=CACHE_TTL_SUMMARY)
    return data


@router.get("/state-breakdown")
async def get_states(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Returns state-wise project aggregations and average risk scores for mapping and spatial surveillance.
    """
    cache_key = "dashboard:state_breakdown"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    data = get_state_breakdown(db=db)
    await set_cache(cache_key, data, ttl_seconds=CACHE_TTL_SUMMARY)
    return data

