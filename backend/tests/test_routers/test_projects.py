"""
SIH 2026 — PS26103 | Projects Router Tests
==========================================
"""

def test_list_projects_default(client):
    """Test GET /api/v1/projects with default pagination."""
    response = client.get("/api/v1/projects?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0
    assert len(data["items"]) <= 10

    # Validate item schema fields
    item = data["items"][0]
    assert "project_uid" in item
    assert "project_name" in item
    assert "ministry" in item
    assert "risk_score" in item
    assert "risk_band" in item


def test_list_projects_filter_risk_band(client):
    """Test filtering projects by risk band (High)."""
    response = client.get("/api/v1/projects?risk_band=High&limit=5")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["risk_band"] == "High"


def test_list_projects_filter_ministry(client):
    """Test filtering projects by ministry name."""
    response = client.get("/api/v1/projects?ministry=Railways&limit=5")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "railway" in item["ministry"].lower()


def test_list_projects_search(client):
    """Test searching across project name or code."""
    response = client.get("/api/v1/projects?search=highway&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)


def test_get_project_detail_and_risk(client):
    """Test GET /api/v1/projects/{uid} and /api/v1/projects/{uid}/risk."""
    # First get a valid project UID
    list_res = client.get("/api/v1/projects?limit=1")
    assert list_res.status_code == 200
    uid = list_res.json()["items"][0]["project_uid"]

    # Detail endpoint
    detail_res = client.get(f"/api/v1/projects/{uid}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["project_uid"] == uid
    assert "latest_metrics" in detail
    assert "risk_assessment" in detail

    # Risk assessment endpoint
    risk_res = client.get(f"/api/v1/projects/{uid}/risk")
    assert risk_res.status_code == 200
    risk = risk_res.json()
    assert risk["project_uid"] == uid
    assert "explanations" in risk


def test_get_project_timeline_history(client):
    """Test GET /api/v1/projects/{uid}/history."""
    list_res = client.get("/api/v1/projects?limit=1")
    uid = list_res.json()["items"][0]["project_uid"]

    response = client.get(f"/api/v1/projects/{uid}/history")
    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)
    assert len(history) > 0
    assert "report_month" in history[0]
    assert "revised_cost_cr" in history[0]


def test_get_nonexistent_project(client):
    """Test 404 behavior for unknown project UID."""
    response = client.get("/api/v1/projects/NON_EXISTENT_UID_99999")
    assert response.status_code == 404

