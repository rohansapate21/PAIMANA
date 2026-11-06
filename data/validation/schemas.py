"""
SIH 2026 — PS26103 | Pandera Data Validation Schemas
=====================================================
Defines strict schema models for project_master and project_month_panel.
"""

try:
    import pandera.pandas as pa
except ImportError:
    import pandera as pa
from pandera.typing import Series


class ProjectMasterSchema(pa.DataFrameModel):
    """Validation schema for project_master.parquet."""
    project_uid: Series[str] = pa.Field(nullable=False, unique=True)
    project_name: Series[str] = pa.Field(nullable=False)
    ministry: Series[str] = pa.Field(nullable=False)
    sector: Series[str] = pa.Field(nullable=False)
    original_cost_cr: Series[float] = pa.Field(ge=0.0, nullable=False)

    class Config:
        coerce = True
        strict = False  # allows metadata/additional columns


class PanelSchema(pa.DataFrameModel):
    """Validation schema for project_month_panel.parquet."""
    project_uid: Series[str] = pa.Field(nullable=False)
    report_month: Series[str] = pa.Field(nullable=False, regex=r"^\d{4}-\d{2}-\d{2}$")
    revised_cost_cr: Series[float] = pa.Field(ge=0.0, nullable=False)
    physical_progress_pct: Series[float] = pa.Field(ge=0.0, le=100.0, nullable=False)
    schedule_delay_months: Series[float] = pa.Field(ge=0.0, nullable=False)
    progress_stagnation_streak: Series[int] = pa.Field(ge=0, nullable=False)
    cost_revision_count: Series[int] = pa.Field(ge=0, nullable=False)

    class Config:
        coerce = True
        strict = False

