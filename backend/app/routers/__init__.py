"""
SIH 2026 — PS26103 | Backend Routers Package
"""

from backend.app.routers.auth import router as auth_router
from backend.app.routers.projects import router as projects_router
from backend.app.routers.alerts import router as alerts_router
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "projects_router",
    "alerts_router",
    "dashboard_router",
    "admin_router",
]
