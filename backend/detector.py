"""Rule-based fault detection for the software service runtime."""
from typing import Any


def _fault(fault_type: str, severity: str, message: str) -> dict[str, str]:
    return {"fault_type": fault_type, "severity": severity, "message": message}


def detect_faults(snapshot: dict[str, Any], config: dict[str, Any]) -> list[dict[str, str]]:
    """Return all faults present in a monitoring snapshot."""
    faults: list[dict[str, str]] = []
    if not snapshot.get("service_running", False):
        faults.append(_fault("SERVICE_FAILURE", "CRITICAL", "The monitored service is not running."))
    if snapshot.get("cpu_usage", 0) > config.get("cpu_threshold", 80):
        faults.append(_fault("CPU_OVERLOAD", "HIGH", "CPU usage exceeded the configured threshold."))
    if snapshot.get("memory_usage", 0) > config.get("memory_threshold", 80):
        faults.append(_fault("MEMORY_OVERLOAD", "HIGH", "Memory usage exceeded the configured threshold."))
    if not snapshot.get("health_ok", False):
        faults.append(_fault("HEALTH_CHECK_FAILURE", "HIGH", "The application health check failed."))
    if snapshot.get("response_failures", 0) >= config.get("response_failure_limit", 3):
        faults.append(_fault("EXCESSIVE_RESPONSE_FAILURES", "HIGH", "Response failures exceeded the configured limit."))
    return faults
