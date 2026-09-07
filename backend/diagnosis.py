"""Translate detected faults into actionable diagnoses."""

DIAGNOSES = {
    "SERVICE_FAILURE": ("The application process may have stopped.", "RESTART_SERVICE"),
    "HEALTH_CHECK_FAILURE": ("The application is not responding correctly.", "REINITIALIZE_SERVICE"),
    "CPU_OVERLOAD": ("The application or system may be consuming excessive CPU.", "CONTROLLED_RESTART"),
    "MEMORY_OVERLOAD": ("Excessive memory consumption was detected.", "CONTROLLED_RESTART"),
    "EXCESSIVE_RESPONSE_FAILURES": ("The service is returning too many failed responses.", "REINITIALIZE_SERVICE"),
}


def diagnose_fault(fault: dict[str, str]) -> dict[str, str]:
    cause, action = DIAGNOSES.get(fault["fault_type"], ("An unknown service fault was detected.", "CONTROLLED_RESTART"))
    return {
        "fault_type": fault["fault_type"],
        "probable_cause": cause,
        "severity": fault.get("severity", "MEDIUM"),
        "recommended_action": action,
    }
