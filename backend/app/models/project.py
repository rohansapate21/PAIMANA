"""
SIH 2026 — PS26103 | SQLAlchemy ORM Models
==========================================
Defines models for projects, panel observations, risk scores, explanations, alerts, and users.
Directly implements Phase 11 schema from the Solution Roadmap.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Text, Float, Integer, BigInteger, Boolean,
    DateTime, ForeignKey, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.app.db.base import Base

# Integer id with BigInteger variant so SQLite uses its native AUTOINCREMENT integer primary key
# while PostgreSQL uses standard 64-bit BIGINT/BIGSERIAL.
AutoId = Integer().with_variant(BigInteger, "postgresql")


class ProjectMaster(Base):
    __tablename__ = "project_master"

    project_uid: Mapped[str] = mapped_column(String(50), primary_key=True)
    original_project_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    implementing_agency: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    ministry: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    sector: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    original_cost_cr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    approval_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    original_completion_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_precision: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="month")
    first_seen_report_month: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_seen_report_month: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    monthly_panel: Mapped[List["ProjectMonthPanel"]] = relationship(
        "ProjectMonthPanel", back_populates="project", cascade="all, delete-orphan"
    )
    risk_scores: Mapped[List["RiskScore"]] = relationship(
        "RiskScore", back_populates="project", cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_master_ministry_sector_state", "ministry", "sector", "state"),
    )


class ProjectMonthPanel(Base):
    __tablename__ = "project_month_panel"

    id: Mapped[int] = mapped_column(AutoId, primary_key=True, autoincrement=True)
    project_uid: Mapped[str] = mapped_column(
        String(50), ForeignKey("project_master.project_uid", ondelete="CASCADE"), nullable=False, index=True
    )
    report_month: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    revised_cost_cr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    expenditure_cr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    physical_progress_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    delta_cost_cr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    delta_progress_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    progress_stagnation_streak: Mapped[int] = mapped_column(Integer, default=0)
    cost_revision_count: Mapped[int] = mapped_column(Integer, default=0)
    schedule_delay_months: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    is_imputed_cost: Mapped[bool] = mapped_column(Boolean, default=False)
    is_imputed_progress: Mapped[bool] = mapped_column(Boolean, default=False)
    outlier_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped["ProjectMaster"] = relationship("ProjectMaster", back_populates="monthly_panel")

    __table_args__ = (
        UniqueConstraint("project_uid", "report_month", name="uq_panel_project_month"),
        Index("idx_panel_month_uid", "report_month", "project_uid"),
    )


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(AutoId, primary_key=True, autoincrement=True)
    project_uid: Mapped[str] = mapped_column(
        String(50), ForeignKey("project_master.project_uid", ondelete="CASCADE"), nullable=False, index=True
    )
    report_month: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_band: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # Low, Medium, High
    ml_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rule_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rule_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    cost_risk_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delay_risk_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shap_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_version: Mapped[str] = mapped_column(String(20), default="v1.0")
    scored_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    project: Mapped["ProjectMaster"] = relationship("ProjectMaster", back_populates="risk_scores")
    explanations: Mapped[List["Explanation"]] = relationship(
        "Explanation", back_populates="risk_score_rel", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("project_uid", "report_month", "model_version", name="uq_risk_project_month_ver"),
        Index("idx_risk_band_score", "report_month", "risk_band", "risk_score"),
    )


class Explanation(Base):
    __tablename__ = "explanations"

    id: Mapped[int] = mapped_column(AutoId, primary_key=True, autoincrement=True)
    risk_score_id: Mapped[int] = mapped_column(
        AutoId, ForeignKey("risk_scores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    shap_value: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    risk_score_rel: Mapped["RiskScore"] = relationship("RiskScore", back_populates="explanations")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(AutoId, primary_key=True, autoincrement=True)
    project_uid: Mapped[str] = mapped_column(
        String(50), ForeignKey("project_master.project_uid", ondelete="CASCADE"), nullable=False, index=True
    )
    report_month: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # rule_triggered, high_risk, stagnation
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # High, Medium, Low
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    project: Mapped["ProjectMaster"] = relationship("ProjectMaster", back_populates="alerts")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(AutoId, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="analyst")  # admin, analyst, viewer
    ministry_scope: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id: Mapped[int] = mapped_column(AutoId, primary_key=True, autoincrement=True)
    report_month: Mapped[str] = mapped_column(String(20), nullable=False)
    rows_extracted: Mapped[int] = mapped_column(Integer, default=0)
    warnings_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS")
    run_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

