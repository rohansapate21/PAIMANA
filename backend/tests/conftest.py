"""
SIH 2026 — PS26103 | Pytest Test Fixtures & Environment
========================================================
Configures database session, FastAPI test client, and authorization headers.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.core.security import create_access_token


@pytest.fixture(scope="session")
def client():
    """Provides a TestClient connected to the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    """Provides an isolated database session per test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def admin_token():
    """Generates a valid JWT token for the admin role."""
    return create_access_token(data={"sub": "admin@mospi.gov.in", "role": "admin"})


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    """Provides Bearer auth headers for the admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def analyst_token():
    """Generates a valid JWT token for the analyst role."""
    return create_access_token(data={"sub": "analyst@mospi.gov.in", "role": "analyst"})


@pytest.fixture(scope="session")
def analyst_headers(analyst_token):
    """Provides Bearer auth headers for the analyst user."""
    return {"Authorization": f"Bearer {analyst_token}"}

