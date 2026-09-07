from backend.recovery import recover, select_recovery_action


def runtime():
    return {"service_running": False, "health_failed": True, "response_failures": 2, "simulated_cpu": 95, "simulated_memory": None, "recovery_attempts": 0}


def test_recovery_action_selection():
    assert select_recovery_action({"recommended_action": "RESTART_SERVICE"}) == "RESTART_SERVICE"


def test_successful_recovery():
    state = runtime()
    result = recover(state, {"recommended_action": "RESTART_SERVICE"})
    assert result["success"] is True
    assert state["service_running"] is True


def test_failed_recovery_is_reported():
    state = runtime()
    result = recover(state, {"recommended_action": "RESTART_SERVICE"}, verifier=lambda _: False)
    assert result["success"] is False
    assert result["result"] == "FAILED"


def test_maximum_retry_protection():
    state = runtime()
    state["recovery_attempts"] = 3
    result = recover(state, {"recommended_action": "RESTART_SERVICE"}, max_attempts=3)
    assert result["result"] == "CRITICAL_FAILURE"
