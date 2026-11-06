"""
SIH 2026 — PS26103 | Dashboard Router Tests
===========================================
"""

def test_dashboard_summary(client):
    """Test GET /api/v1/dashboard/summary."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_projects" in data
    assert "active_scored_projects" in data
    assert "high_risk_count" in data
    assert "medium_risk_count" in data
    assert "low_risk_count" in data
    assert "total_original_cost_cr" in data
    assert "total_revised_cost_cr" in data
    assert "avg_schedule_delay_months" in data
    assert data["total_projects"] > 0
    assert data["active_scored_projects"] > 0


def test_dashboard_ministry_breakdown(client):
    """Test GET /api/v1/dashboard/ministry-breakdown."""
    response = client.get("/api/v1/dashboard/ministry-breakdown")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first = data[0]
    assert "ministry" in first
    assert "total_projects" in first
    assert "high_risk_count" in first
    assert "avg_risk_score" in first


def test_dashboard_risk_trend(client):
    """Test GET /api/v1/dashboard/risk-trend."""
    response = client.get("/api/v1/dashboard/risk-trend")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "report_month" in data[0]
    assert "High" in data[0]
    assert "Medium" in data[0]
    assert "Low" in data[0]

