"""
SIH 2026 — PS26103 | Alerts Router Tests
========================================
"""

def test_list_alerts(client):
    """Test GET /api/v1/alerts."""
    response = client.get("/api/v1/alerts?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        item = data["items"][0]
        assert "id" in item
        assert "project_uid" in item
        assert "severity" in item
        assert "reason" in item


def test_list_alerts_filter_severity(client):
    """Test filtering alerts by severity."""
    response = client.get("/api/v1/alerts?severity=High&limit=5")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["severity"] == "High"


def test_get_alerts_summary(client):
    """Test GET /api/v1/alerts/summary."""
    response = client.get("/api/v1/alerts/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_active_alerts" in data
    assert "by_severity" in data
    assert "by_type" in data
    assert "High" in data["by_severity"]


def test_acknowledge_alert(client):
    """Test PATCH /api/v1/alerts/{id}/acknowledge."""
    # First get an existing alert
    list_res = client.get("/api/v1/alerts?limit=1")
    assert list_res.status_code == 200
    alerts = list_res.json()["items"]
    if alerts:
        alert_id = alerts[0]["id"]
        ack_res = client.patch(f"/api/v1/alerts/{alert_id}/acknowledge")
        assert ack_res.status_code == 200
        ack_data = ack_res.json()
        assert ack_data["id"] == alert_id
        assert ack_data["acknowledged"] is True
        assert "acknowledged_at" in ack_data

