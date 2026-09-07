"""Health checks for the simulated service and host resources."""
from typing import Any


def check_health(snapshot: dict[str, Any]) -> dict[str, Any]:
    healthy = bool(snapshot.get("service_running")) and bool(snapshot.get("health_ok"))
    return {
        "healthy": healthy,
        "status": "RUNNING" if healthy else "DEGRADED",
        "service_running": bool(snapshot.get("service_running")),
        "response_ok": bool(snapshot.get("health_ok")),
    }
