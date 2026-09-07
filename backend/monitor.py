"""Low-overhead host and application monitoring."""
from typing import Any
import psutil


def collect_metrics(runtime: dict[str, Any]) -> dict[str, Any]:
    """Collect host metrics and combine them with the simulated service state."""
    process = psutil.Process()
    return {
        "cpu_usage": round(psutil.cpu_percent(interval=None), 2) if not runtime.get("simulated_cpu") else runtime["simulated_cpu"],
        "memory_usage": round(psutil.virtual_memory().percent, 2) if not runtime.get("simulated_memory") else runtime["simulated_memory"],
        "service_running": runtime.get("service_running", True),
        "health_ok": runtime.get("service_running", True) and not runtime.get("health_failed", False),
        "response_failures": runtime.get("response_failures", 0),
        "process_id": process.pid,
    }
