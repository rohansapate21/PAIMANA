"""
SIH 2026 — PS26103 | Authentication Router Tests
================================================
"""

def test_login_success(client):
    """Test login with valid administrator credentials."""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@mospi.gov.in",
        "password": "Admin@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@mospi.gov.in"
    assert data["user"]["role"] == "admin"


def test_login_invalid_password(client):
    """Test login with invalid password returns 401."""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@mospi.gov.in",
        "password": "WrongPassword!999"
    })
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_invalid_user(client):
    """Test login with unknown email returns 401."""
    response = client.post("/api/v1/auth/login", json={
        "email": "unknown_user@mospi.gov.in",
        "password": "Password@123"
    })
    assert response.status_code == 401


def test_get_current_user_profile(client, admin_headers):
    """Test GET /api/v1/auth/me with valid Bearer token."""
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@mospi.gov.in"
    assert data["role"] == "admin"


def test_get_current_user_profile_unauthorized(client):
    """Test GET /api/v1/auth/me without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

