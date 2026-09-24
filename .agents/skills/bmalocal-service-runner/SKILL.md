---
name: bmalocal-service-runner
description: >-
  Starting, stopping, and diagnosing the local Anvil App Server, Java
  runtime, WebSocket server, SSL certificates, and wkhtmltopdf for BMALocal.
  Use when debugging port conflicts, server startup failures, or inspecting
  logs/, or when preparing the environment to run the test suite.
---

# BMALocal Service Runner & Environment Management

This skill governs the local execution environment, dependency validation, service orchestration, and runtime troubleshooting for the Anvil App Server and WebSocket daemon.

---

## 1. System Dependencies & Startup Sequence

BMALocal relies on the following local runtime components:
1. **Java Runtime (JRE/JDK 8+)**: Required by the open-source Anvil App Server core.
2. **MySQL Server 8.0**: Transactional database running on port `3306`.
3. **Python Virtual Environment (`venv`)**: Provides `anvil-app-server`, `websockets`, `mysql-connector-python`.
4. **wkhtmltopdf**: Command-line binary for generating high-fidelity PDF invoices and job card sign-offs.
5. **SSL/TLS Certificates**: Local certificates generated via `mkcert` in [cert/](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/cert).

### Service Startup Order
```text
1. Prerequisite Check (scripts/check-prereqs.ps1)
       │
       ▼
2. MySQL Database Service (Port 3306)
       │
       ▼
3. Anvil App Server (HTTP on 8080 or HTTPS on 443)
       │
       ▼
4. Walkie-Talkie WebSocket Daemon (Port 8765, started in daemon thread by BMALocal.py)
```

---

## 2. Automated Prerequisite Verification Script

Run the verification script before starting the stack or launching tests:
```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/bmalocal-service-runner/scripts/check-prereqs.ps1
```
The script verifies:
- Java version installed and on `PATH`.
- Ports `8080` (or `443`), `8765`, and `3306` availability.
- SSL certificates exist and have not expired.
- `wkhtmltopdf` binary exists at the configured path in [.env](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.env).
- MySQL database connectivity.

---

## 3. Unified Local Launcher Script

Launch the full stack with [scripts/start-local.ps1](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-service-runner/scripts/start-local.ps1):

```powershell
# Standard local development run
powershell -ExecutionPolicy Bypass -File .agents/skills/bmalocal-service-runner/scripts/start-local.ps1

# Run in test mode (points to isolated test database for Playwright/pytest)
powershell -ExecutionPolicy Bypass -File .agents/skills/bmalocal-service-runner/scripts/start-local.ps1 -forTests
```

---

## 4. Log Inspection & Troubleshooting

Logs are located in [logs/](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/logs):
- **[logs/service_output.log](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/logs/service_output.log)**: Anvil App Server stdout/stderr, database connection errors, Python stack traces.
- **[logs/chat_ws_server.log](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/logs/chat_ws_server.log)**: WebSocket client connections, audio streaming errors, chat message broadcasts.

### Recognizing Healthy vs. Failing Logs
- **Healthy Startup**:
  `[INFO anvil.app-server.core] App server listening on port 8080`  
  `[*] Walkie Talkie WebSocket Server starting on ws://0.0.0.0:8765`  
  `[+] Server is listening on ws://0.0.0.0:8765`
- **Port Conflict / Failed Startup**:
  `Address already in use: bind` &rarr; Terminate zombie Python or Anvil processes on port 8080/8765:
  ```powershell
  # Find process using port 8765 or 8080
  Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | Select-Object OwningProcess
  ```
- **Database Connection Failure**:
  `mysql.connector.errors.DatabaseError: 2003: Can't connect to MySQL server` &rarr; Verify MySQL Windows service (`MySQL80`) is running.
