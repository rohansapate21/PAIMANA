"""
SIH 2026 — PS26103 | FastAPI Production Backend
===============================================
Main application entry point providing REST endpoints for:
- JWT Authentication & RBAC
- Project Risk Scoring, History & SHAP Explainability
- Proactive Early Warning Alerts & Acknowledgment
- Executive Dashboard KPIs & Ministry Aggregations
- Automated Data Ingestion & Model Retraining Admin Tasks
"""

import sys
from pathlib import Path

# Ensure project root is in python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn

# Prometheus metrics instrumentation (prometheus_fastapi_instrumentator)
# Exposes /metrics endpoint consumed by prometheus.yml scrape config.
# Gracefully skips if the package is not installed (dev/test environments).
try:
    from prometheus_fastapi_instrumentator import Instrumentator as _Instrumentator
    _PROMETHEUS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_fastapi_instrumentator not installed – /metrics endpoint disabled")

from backend.app.core.config import settings
from backend.app.routers.auth import router as auth_router
from backend.app.routers.projects import router as projects_router
from backend.app.routers.alerts import router as alerts_router
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.admin import router as admin_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="MoSPI Infrastructure Monitoring & Predictive Early Warning Analytics Platform",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cross-Origin Resource Sharing (CORS) Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in dev; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire Prometheus instrumentation – must happen AFTER CORS middleware is added
# so the /metrics endpoint inherits correct headers, and BEFORE routers so all
# routes are automatically tracked.
if _PROMETHEUS_AVAILABLE:
    _Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/docs", "/redoc", "/openapi.json"],
        inprogress_labels=True,
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    logger.info("Prometheus metrics endpoint exposed at /metrics")

# Register API v1 Routers
api_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=api_prefix)
app.include_router(projects_router, prefix=api_prefix)
app.include_router(alerts_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)


@app.get("/", tags=["System"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "PAIMANA AI Infrastructure Backend",
        "version": settings.VERSION
    }


if __name__ == "__main__":
    logger.info(f"Starting {settings.PROJECT_NAME} on http://0.0.0.0:8000...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
