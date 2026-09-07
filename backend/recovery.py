"""Controlled recovery actions with retry protection."""
from typing import Any, Callable


def select_recovery_action(diagnosis: dict[str, str]) -> str:
    return diagnosis.get("recommended_action", "CONTROLLED_RESTART")


def recover(runtime: dict[str, Any], diagnosis: dict[str, str], max_attempts: int = 3, verifier: Callable[[dict[str, Any]], bool] | None = None) -> dict[str, Any]:
    """Perform one bounded recovery attempt and verify the resulting runtime."""
    attempts = int(runtime.get("recovery_attempts", 0))
    if attempts >= max_attempts:
        return {"success": False, "result": "CRITICAL_FAILURE", "action": select_recovery_action(diagnosis), "attempts": attempts}

    action = select_recovery_action(diagnosis)
    runtime["recovery_attempts"] = attempts + 1
    runtime["service_running"] = True
    runtime["health_failed"] = False
    runtime["response_failures"] = 0
    runtime["simulated_cpu"] = None
    runtime["simulated_memory"] = None
    success = verifier(runtime) if verifier else bool(runtime.get("service_running")) and not runtime.get("health_failed", False)
    if success:
        runtime["recovery_attempts"] = 0
    return {"success": success, "result": "SUCCESS" if success else "FAILED", "action": action, "attempts": runtime["recovery_attempts"] if not success else attempts + 1}
