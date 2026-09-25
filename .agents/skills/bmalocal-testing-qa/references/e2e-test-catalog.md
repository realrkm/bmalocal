# BMALocal End-to-End Test Journey Catalog

This catalog documents the critical user journeys tested via Playwright across Desktop, Tablet, and Mobile viewports.

---

## 1. Critical User Journeys

| Journey ID | Name / Flow | Key Steps | Breakpoints Covered | Guards Against | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-01** | **User Authentication** | 1. Navigate to `/`<br>2. Enter credentials<br>3. Verify dashboard loads<br>4. Test password toggle | Desktop, Tablet, Mobile | Login lockouts, broken toggle, session drops | **Implemented** (`tests/e2e/test_auth_flow.py`) |
| **E2E-02** | **Job Card Lifecycle** | 1. Create Job Card with VIN/Reg<br>2. Link technician assignment<br>3. Advance status to In-Service & log work<br>4. Sign off with binary signature & complete | Desktop, Mobile (Floor), API | Broken status transitions, missing mandatory fields, unindexed query stalls | **Implemented** (`tests/e2e/test_jobcard_lifecycle.py`) |
| **E2E-03** | **Invoice Generation** | 1. Convert completed Job Card to Invoice<br>2. Add parts & labor<br>3. Verify totals and tax<br>4. Save & preview PDF | Desktop, Tablet, Engine | Calculation rounding errors, broken PDF generation | **Implemented** (`tests/e2e/test_invoice_generation.py`) |
| **E2E-04** | **Contact Management** | 1. Search client by phone/reg<br>2. Create new client record<br>3. Link to vehicle profile | Desktop, Tablet, Mobile | Search failure, duplicate entries | Planned |
| **E2E-05** | **Realtime Chat & Walkie Talkie** | 1. Connect & join with auth handshake<br>2. Synchronize history & presence<br>3. Bidirectional text broadcast<br>4. MySQL persistence & read receipts<br>5. Message editing & disconnects | Network / WebSocket Daemon | WebSocket connection drops, chat desync, data loss | **Implemented** (`tests/e2e/test_realtime_chat.py`) |

---

## 2. Playwright & E2E Test Execution Commands

```powershell
# Run all E2E tests against local test server using project venv
d:\BMAAutoAccessories\venv\Scripts\python.exe -m pytest tests/e2e/

# Run specifically on Job Card lifecycle test suite
d:\BMAAutoAccessories\venv\Scripts\python.exe -m pytest tests/e2e/test_jobcard_lifecycle.py -v

# Run specifically on Invoice generation & PDF engine tests
d:\BMAAutoAccessories\venv\Scripts\python.exe -m pytest tests/e2e/test_invoice_generation.py -v

# Run specifically on realtime chat & walkie-talkie WebSocket tests
d:\BMAAutoAccessories\venv\Scripts\python.exe -m pytest tests/e2e/test_realtime_chat.py -v

# Run specifically on authentication / viewport browser tests
d:\BMAAutoAccessories\venv\Scripts\python.exe -m pytest tests/e2e/test_auth_flow.py -v

# Run with headed browser window for visual observation
d:\BMAAutoAccessories\venv\Scripts\python.exe -m pytest tests/e2e/ --headed
```
