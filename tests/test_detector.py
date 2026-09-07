from backend.detector import detect_faults

CONFIG = {"cpu_threshold": 80, "memory_threshold": 80, "response_failure_limit": 3}


def test_cpu_overload_detection():
    faults = detect_faults({"service_running": True, "health_ok": True, "cpu_usage": 91, "memory_usage": 20}, CONFIG)
    assert any(fault["fault_type"] == "CPU_OVERLOAD" for fault in faults)


def test_memory_overload_detection():
    faults = detect_faults({"service_running": True, "health_ok": True, "cpu_usage": 20, "memory_usage": 91}, CONFIG)
    assert any(fault["fault_type"] == "MEMORY_OVERLOAD" for fault in faults)


def test_service_failure_detection():
    faults = detect_faults({"service_running": False, "health_ok": False, "cpu_usage": 20, "memory_usage": 20}, CONFIG)
    assert {fault["fault_type"] for fault in faults} >= {"SERVICE_FAILURE", "HEALTH_CHECK_FAILURE"}


def test_normal_condition_has_no_faults():
    assert detect_faults({"service_running": True, "health_ok": True, "cpu_usage": 20, "memory_usage": 20}, CONFIG) == []
