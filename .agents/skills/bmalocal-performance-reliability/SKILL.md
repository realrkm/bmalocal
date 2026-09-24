---
name: bmalocal-performance-reliability
description: >-
  Performance, efficiency, and reliability standards for BMALocal — query and
  call latency budgets, caching, error handling/retries, and monitoring. Use
  for any change touching database queries, server callables, page load, or
  the realtime connection, and whenever a change could affect app speed or
  uptime.
---

# BMALocal Performance, Efficiency & Reliability Standards

This skill governs latency budgets, database query efficiency, fault resilience, transaction integrity, and proactive log monitoring for BMALocal.

---

## 1. Standing Monitoring Pass (ADLC Continuous Feedback)

> **At the start of any work session touching BMALocal, or upon explicit request:**
> 1. Review [logs/service_output.log](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/logs/service_output.log) and [logs/chat_ws_server.log](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/logs/chat_ws_server.log) for recurring error patterns, unhandled exceptions, port collisions, or connection timeouts.
> 2. Check for MySQL slow query warnings or aborted connection spikes.
> 3. Log any newly discovered defect patterns in the appropriate skill's `common-*-errors.md` and write a reproducing test before fixing.

---

## 2. Latency Budgets & Target Benchmarks

Keep operations strictly within these latency limits on standard workshop hardware:

| User Operation | Max Acceptable Latency | Implementation Pattern |
| :--- | :--- | :--- |
| **Instant Search (Contacts / Reg / Part)** | `< 300 ms` | Indexed `LIKE 'prefix%'` or exact index lookups; debounce client keystrokes by `250ms` |
| **Job Card List Load** | `< 1000 ms` | Server-side pagination (`LIMIT %s OFFSET %s`); select specific columns, never `SELECT *` |
| **Job Card Save / Status Transition** | `< 500 ms` | Single atomic transaction in `db_cursor()`, no external network calls inside transaction |
| **Invoice Save & Calculation** | `< 500 ms` | Batch insertion of line items; calculate totals in memory before committing |
| **PDF Generation (wkhtmltopdf)** | `< 2500 ms` | Asynchronous worker or background task; show spinner with cancel option |

---

## 3. Database Query Efficiency

- **Index Enforcement**: Every query filtering or sorting on `ChassisNo`, `RegistrationNo`, `ClientContactID`, `Status`, or `CreatedAt` must be backed by an index in [references/schema.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-database-ops/references/schema.md).
- **No N+1 Queries**: Never execute a database query inside a Python loop.
  - **Forbidden**: Looping over 50 job cards and executing `SELECT * FROM tbl_assignedcarparts WHERE JobCardID = %s` for each.
  - **Mandatory**: Use a `JOIN` or fetch all related parts with `WHERE JobCardID IN (%s, %s, ...)` and assemble in memory.
- **Strict Column Selection**: Never use `SELECT *` on high-volume tables (`tbl_jobcarddetails`, `tbl_invoices`, `tbl_stockparts`). Request only the specific columns needed by the calling UI.
- **Unbounded Lists Must Be Paginated**: All tables, repeating panels, and reports that can exceed 50 items must implement pagination.

---

## 4. Connection Pooling & Resource Cleanup

- Always use the `db_cursor()` context manager from [server_code/BMALocal.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/server_code/BMALocal.py#L90-L102).
- The context manager guarantees:
  1. Connection is retrieved from `_db_pool`.
  2. Transaction commits automatically on success.
  3. Transaction rolls back automatically on error.
  4. Both cursor and connection are safely returned to the pool in the `finally:` block.
- Leaked connections exhaust the pool (`pool_size=5`), causing all subsequent user requests to stall.

---

## 5. Resilience & Fault Tolerance

1. **Client-Side Server Call Wrappers**:
   - Wrap client-side calls in `try...except` handling `anvil.server.AppOfflineError`:
     ```python
     try:
         result = anvil.server.call("update_job_status", job_id, status)
     except anvil.server.AppOfflineError:
         anvil.Notification("Local server is unreachable. Check network.", style="danger").show()
     except Exception as e:
         anvil.Notification(f"Error: {e}", style="warning").show()
     ```
2. **WebSocket Reconnect with Exponential Backoff**:
   - The Walkie-Talkie client in [walkietalkie.js](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/assets/walkietalkie.js) must reconnect with backoff (`1s`, `2s`, `4s`, max `10s`) upon unexpected disconnects, rather than flooding the port or halting silently.
3. **Atomic Operations**: Multi-table updates (e.g. closing a Job Card and generating an Invoice) must run inside a single transaction so that partial failures rollback completely.
