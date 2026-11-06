"""
SIH 2026 — PS26103 | Alerting Service Unit Tests
================================================
"""

from backend.app.services.alerting import (
    get_active_alerts,
    acknowledge_alert,
    generate_alerts_for_month,
    get_alert_summary
)


def test_service_get_active_alerts(db_session):
    """Test get_active_alerts service function."""
    result = get_active_alerts(db_session, limit=10)
    assert "items" in result
    assert "total" in result
    assert isinstance(result["items"], list)


def test_service_get_alert_summary(db_session):
    """Test get_alert_summary service function."""
    summary = get_alert_summary(db_session)
    assert "total_active_alerts" in summary
    assert "by_severity" in summary
    assert "by_type" in summary


def test_service_generate_alerts_deduplication(db_session):
    """Test that generating alerts for an already scored month does not create duplicate entries."""
    # Since alerts were already hydrated for 2026-08-01, re-running should return 0 new alerts
    new_alerts = generate_alerts_for_month(db_session, report_month="2026-08-01")
    assert new_alerts == 0


def test_service_acknowledge_alert(db_session):
    """Test acknowledge_alert service function."""
    alerts = get_active_alerts(db_session, limit=1)
    if alerts["items"]:
        alert_id = alerts["items"][0]["id"]
        ack = acknowledge_alert(db_session, alert_id)
        assert ack is not None
        assert ack["acknowledged"] is True

