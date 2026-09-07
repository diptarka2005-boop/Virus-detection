"""FastAPI application for the self-healing computing prototype."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.detector import detect_faults
from backend.diagnosis import diagnose_fault
from backend.health_check import check_health
from backend.logger import get_logger, log_event
from backend.monitor import collect_metrics
from backend.recovery import recover

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "config.json"
DATABASE_PATH = ROOT / "database" / "system.db"
LOG_PATH = ROOT / "logs" / "system.log"
MAX_METRIC_RECORDS = 10_000

with CONFIG_PATH.open(encoding="utf-8") as config_file:
    CONFIG: dict[str, Any] = json.load(config_file)

logger = get_logger(LOG_PATH)
runtime: dict[str, Any] = {
    "service_running": True,
    "health_failed": False,
    "response_failures": 0,
    "simulated_cpu": None,
    "simulated_memory": None,
    "recovery_attempts": 0,
    "monitoring": True,
}
state_lock = threading.RLock()
monitor_thread: threading.Thread | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connection() -> sqlite3.Connection:
    # The monitor thread and API requests can write at the same time.  Waiting
    # briefly and using WAL mode prevents transient "database is locked" errors.
    db = sqlite3.connect(DATABASE_PATH, timeout=10)
    db.execute("PRAGMA busy_timeout = 10000")
    db.execute("PRAGMA foreign_keys = ON")
    db.row_factory = sqlite3.Row
    return db


def initialize_database() -> None:
    with connection() as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS faults (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            fault_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            diagnosis TEXT,
            status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS recovery_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            fault_id INTEGER,
            action TEXT NOT NULL,
            result TEXT NOT NULL,
            recovery_time REAL NOT NULL,
            attempts INTEGER NOT NULL,
            FOREIGN KEY (fault_id) REFERENCES faults(id)
        );
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cpu_usage REAL NOT NULL,
            memory_usage REAL NOT NULL,
            service_status TEXT NOT NULL
        );
        """)


def save_metrics(metrics: dict[str, Any]) -> None:
    with connection() as db:
        db.execute("INSERT INTO system_metrics (timestamp, cpu_usage, memory_usage, service_status) VALUES (?, ?, ?, ?)", (utc_now(), metrics["cpu_usage"], metrics["memory_usage"], "RUNNING" if metrics["service_running"] else "STOPPED"))
        db.execute("DELETE FROM system_metrics WHERE id NOT IN (SELECT id FROM system_metrics ORDER BY id DESC LIMIT ?)", (MAX_METRIC_RECORDS,))


def process_fault(fault: dict[str, str], auto_recover: bool = True) -> dict[str, Any]:
    diagnosis = diagnose_fault(fault)
    log_event(logger, "FAULT_DETECTED", fault["fault_type"])
    log_event(logger, "FAULT_DIAGNOSED", diagnosis["probable_cause"])
    with connection() as db:
        cursor = db.execute("INSERT INTO faults (timestamp, fault_type, severity, description, diagnosis, status) VALUES (?, ?, ?, ?, ?, ?)", (utc_now(), fault["fault_type"], fault["severity"], fault["message"], diagnosis["probable_cause"], "DETECTED"))
        fault_id = cursor.lastrowid
    result: dict[str, Any] = {"fault_id": fault_id, "fault": fault, "diagnosis": diagnosis}
    if auto_recover:
        result["recovery"] = perform_recovery(diagnosis, fault_id)
    return result


def perform_recovery(diagnosis: dict[str, str], fault_id: int | None = None) -> dict[str, Any]:
    log_event(logger, "RECOVERY_STARTED", diagnosis["recommended_action"])
    started = time.perf_counter()
    with state_lock:
        result = recover(runtime, diagnosis, int(CONFIG["max_recovery_attempts"]))
    elapsed = round(time.perf_counter() - started, 4)
    event_result = result["result"]
    with connection() as db:
        db.execute("INSERT INTO recovery_events (timestamp, fault_id, action, result, recovery_time, attempts) VALUES (?, ?, ?, ?, ?, ?)", (utc_now(), fault_id, result["action"], event_result, elapsed, result["attempts"]))
        if fault_id:
            db.execute("UPDATE faults SET status = ? WHERE id = ?", ("RECOVERED" if result["success"] else event_result, fault_id))
    log_event(logger, "RECOVERY_SUCCESS" if result["success"] else ("CRITICAL_FAILURE" if event_result == "CRITICAL_FAILURE" else "RECOVERY_FAILED"), event_result)
    return {**result, "recovery_time": elapsed}


def monitor_loop() -> None:
    log_event(logger, "SYSTEM_STARTED")
    while runtime["monitoring"]:
        with state_lock:
            metrics = collect_metrics(runtime)
        save_metrics(metrics)
        faults = detect_faults(metrics, CONFIG)
        for fault in faults:
            process_fault(fault, auto_recover=True)
        time.sleep(float(CONFIG["monitor_interval"]))


@asynccontextmanager
async def lifespan(_: FastAPI):
    global monitor_thread
    initialize_database()
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    yield
    runtime["monitoring"] = False


app = FastAPI(title="Self-Healing Computing System", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "Self-Healing Computing System", "message": "Software-level self-healing prototype", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, Any]:
    with state_lock:
        return check_health(collect_metrics(runtime))


@app.get("/status")
def status() -> dict[str, Any]:
    with state_lock:
        metrics = collect_metrics(runtime)
    health_result = check_health(metrics)
    with connection() as db:
        fault_count = db.execute("SELECT COUNT(*) FROM faults").fetchone()[0]
        recovery_count = db.execute("SELECT COUNT(*) FROM recovery_events WHERE result = 'SUCCESS'").fetchone()[0]
        failed_count = db.execute("SELECT COUNT(*) FROM recovery_events WHERE result != 'SUCCESS'").fetchone()[0]
    return {"status": "HEALTHY" if health_result["healthy"] else ("CRITICAL" if not metrics["service_running"] else "DEGRADED"), "health": health_result, "metrics": metrics, "fault_count": fault_count, "recovery_count": recovery_count, "failed_recovery_count": failed_count}


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    with state_lock:
        snapshot = collect_metrics(runtime)
    return snapshot


@app.get("/faults")
def faults() -> list[dict[str, Any]]:
    with connection() as db:
        return [dict(row) for row in db.execute("SELECT * FROM faults ORDER BY id DESC LIMIT 25")]


@app.get("/recovery-history")
def recovery_history() -> list[dict[str, Any]]:
    with connection() as db:
        return [dict(row) for row in db.execute("SELECT * FROM recovery_events ORDER BY id DESC LIMIT 25")]


@app.post("/simulate/crash")
def simulate_crash() -> dict[str, str]:
    with state_lock:
        runtime.update(service_running=False, health_failed=True)
    log_event(logger, "SIMULATION_CRASH")
    return {"message": "Controlled service crash simulated."}


@app.post("/simulate/high-cpu")
def simulate_high_cpu() -> dict[str, Any]:
    with state_lock:
        runtime["simulated_cpu"] = min(99, max(81, CONFIG["cpu_threshold"] + 5))
    log_event(logger, "SIMULATION_HIGH_CPU")
    return {"message": "Controlled high CPU condition simulated.", "cpu_usage": runtime["simulated_cpu"]}


@app.post("/simulate/high-memory")
def simulate_high_memory() -> dict[str, Any]:
    with state_lock:
        runtime["simulated_memory"] = min(99, max(81, CONFIG["memory_threshold"] + 5))
    log_event(logger, "SIMULATION_HIGH_MEMORY")
    return {"message": "Controlled high memory condition simulated.", "memory_usage": runtime["simulated_memory"]}


@app.post("/recover")
def manual_recover() -> dict[str, Any]:
    with state_lock:
        metrics = collect_metrics(runtime)
    faults_found = detect_faults(metrics, CONFIG)
    if not faults_found:
        return {"message": "No active fault requires recovery.", "recovery": None}
    return process_fault(faults_found[0], auto_recover=True)


@app.post("/reset")
def reset() -> dict[str, str]:
    with state_lock:
        runtime.update(service_running=True, health_failed=False, response_failures=0, simulated_cpu=None, simulated_memory=None, recovery_attempts=0)
    with connection() as db:
        db.execute("UPDATE faults SET status = 'RESET' WHERE status IN ('DETECTED', 'CRITICAL_FAILURE', 'FAILED')")
    log_event(logger, "SYSTEM_RESET")
    return {"message": "System runtime reset successfully."}
