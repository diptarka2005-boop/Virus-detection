# Self-Healing Computing Elements

## Problem Statement
Production software can fail through stopped services, resource overload, or unhealthy responses. Detecting and recovering from these conditions manually increases downtime and delays diagnosis.

## Project Objective
This project demonstrates a complete software-level workflow: **Monitor -> Detect -> Diagnose -> Recover -> Verify -> Log**. It monitors a local application runtime, classifies faults, chooses a bounded recovery action, verifies the result, and stores the event history.

This is a college-level software prototype. It does not physically repair a CPU, computer hardware, or an operating system.

## Why Self-Healing Computing Is Needed
Automated detection and recovery can reduce service downtime, make operational behavior observable, and provide repeatable responses to known failures. Bounded retries and critical-failure reporting are included so automation does not become an endless restart loop.

## Features
- FastAPI REST API with CORS enabled
- Configurable CPU, memory, response-failure, interval, and retry thresholds
- SQLite persistence for faults, recovery events, and metrics
- `psutil` host telemetry
- Controlled crash, high CPU, and high memory simulations scoped to application state
- Diagnosis and bounded recovery with verification
- Responsive vanilla HTML/CSS/JavaScript dashboard
- Pytest coverage for detection, recovery, retry protection, and health checks

## System Architecture
1. `monitor.py` samples host metrics and the simulated service state.
2. `detector.py` compares the snapshot with `config/config.json` thresholds.
3. `diagnosis.py` maps each fault to a probable cause and action.
4. `recovery.py` performs a controlled runtime reset and verifies health.
5. `logger.py` writes lifecycle events to `logs/system.log`.
6. `app.py` stores durable records in SQLite and serves the API.
7. `frontend/` displays current telemetry and event history.

## Technology Stack
Python 3.11+, FastAPI, Uvicorn, psutil, SQLite, Python logging, pytest, HTML5, CSS3, and vanilla JavaScript.

## Folder Structure
```text
Self-Healing-Computing/
├── backend/       # API and modular self-healing engine
├── frontend/      # dashboard
├── database/      # SQLite database created/initialized at startup
├── logs/          # system.log
├── tests/         # pytest tests
├── config/        # JSON configuration
├── requirements.txt
├── run.py
└── README.md
```

## Installation
From the `Self-Healing-Computing` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The virtual environment isolates FastAPI, Uvicorn, psutil, HTTPX, and pytest from the rest of the machine. SQLite is included with Python.

## How to Run
```powershell
python run.py
```

Open `frontend/index.html` in a browser after the API is running. The frontend expects `http://127.0.0.1:8000`. For a browser that blocks local file requests, serve the frontend directory with a simple static server, such as `python -m http.server 5500 --directory frontend`, and open `http://127.0.0.1:5500`.

The API docs are available at `http://127.0.0.1:8000/docs`.

## API Documentation
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Project identity and docs link |
| GET | `/health` | Current health result |
| GET | `/status` | Status, metrics, and event counts |
| GET | `/metrics` | Current telemetry snapshot |
| GET | `/faults` | Recent fault records |
| GET | `/recovery-history` | Recent recovery records |
| POST | `/simulate/crash` | Stop the simulated service |
| POST | `/simulate/high-cpu` | Set simulated CPU above threshold |
| POST | `/simulate/high-memory` | Set simulated memory above threshold |
| POST | `/recover` | Manually recover the first active fault |
| POST | `/reset` | Restore the simulated runtime |

## Dashboard
The dashboard presents system status, live CPU and memory metrics, service and health state, event counts, the fault register, and recovery history. Controls invoke real API endpoints. It refreshes telemetry every four seconds without reloading the page.

## Fault Detection, Diagnosis, and Recovery
A service crash changes only the in-memory runtime state. The monitor sees the unhealthy snapshot and the detector emits `SERVICE_FAILURE` and `HEALTH_CHECK_FAILURE`. Diagnosis supplies a probable cause and recovery action. Recovery resets the simulated runtime, checks the result, writes a recovery event, and updates the fault status. Failed attempts are bounded by `max_recovery_attempts`; exceeding that limit creates a `CRITICAL_FAILURE` record.

## Database Structure
`database/system.db` is initialized automatically. It contains:
- `faults`: timestamp, type, severity, description, diagnosis, and status.
- `recovery_events`: linked fault, action, result, duration, and attempts.
- `system_metrics`: timestamped CPU, memory, and service status samples.

## Testing
```powershell
pytest
```

The tests cover CPU and memory overloads, service failure, normal conditions, recovery selection, success and failure, maximum retries, and health responses.

## Demonstration Procedure
1. Start the API with `python run.py`.
2. Open `frontend/index.html`.
3. Click **Simulate crash**, then observe the fault and recovery records.
4. Click **Simulate high CPU** or **Simulate high memory** to demonstrate threshold detection.
5. Inspect `/docs`, the dashboard, `database/system.db`, and `logs/system.log`.
6. Click **Reset system** to return the runtime to a healthy baseline.

## Limitations
The service is simulated in application memory, so it does not restart an external process. Host metrics are sampled through `psutil`, while demonstration overload values are controlled signals. The rule-based detector has no machine learning model and is intended for education, testing, and extension.

## Future Improvements
Possible extensions include external process supervision, authentication, configurable alert destinations, richer trend charts, persistent configuration editing, a real worker service, and optional anomaly detection trained on historical metrics.
