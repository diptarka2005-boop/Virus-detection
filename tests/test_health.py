from backend.health_check import check_health


def test_healthy_service():
    result = check_health({"service_running": True, "health_ok": True})
    assert result == {"healthy": True, "status": "RUNNING", "service_running": True, "response_ok": True}


def test_failed_health_check():
    result = check_health({"service_running": True, "health_ok": False})
    assert result["healthy"] is False
    assert result["status"] == "DEGRADED"


def test_status_response_for_stopped_service():
    result = check_health({"service_running": False, "health_ok": False})
    assert result["service_running"] is False
    assert result["status"] == "DEGRADED"
