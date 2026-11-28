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
| **Modal / Subform Open (Cached / Pre-warmed)** | `< 16 ms` (`0` click RPCs) | Atomic single-RPC bundle + idle/hover pre-warmed form instances + in-place modal swap |
| **Hub / Section / Recent Entity Switch** | `< 50 ms` | Lazy subform imports, bounded client LRU cache, and `_load_seq` stale-response guard |
| **Instant Search (Contacts / Reg / Part)** | `< 300 ms` | Indexed `LIKE 'prefix%'` or exact index lookups; speculative warm of `result[0]` |
| **Job Card List Load** | `< 1000 ms` | Server-side pagination (`LIMIT %s OFFSET %s`); select specific columns, never `SELECT *` |
| **Job Card Save / Status Transition** | `< 500 ms` | Single atomic transaction in `db_cursor()`, non-blocking `publish_realtime_event()` |
| **Invoice Save & Calculation** | `< 500 ms` | Batch insertion of line items; calculate totals in memory before committing |
| **PDF Generation (wkhtmltopdf)** | `< 2500 ms` | Lazy-load `pdfkit` via `get_pdfkit()`; disable trigger button with `finally:` re-enable |

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

---

## 6. Instant Form & Modal Loading Playbook (Server + Client)

Use this checklist whenever optimizing slow or intermittently sluggish forms/modals (reference implementation: [job_cards.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/server_code/job_cards.py), [ProgressTracker/\_\_init\_\_.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/ProgressTracker/__init__.py), [JobCardForm/\_\_init\_\_.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/JobCardForm/__init__.py), [EditJobCard/\_\_init\_\_.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/EditJobCard/__init__.py)):

1. **Single-RPC, Single-Cursor Atomic Bootstrap**:
   - Collapse multi-call form initializations (e.g., 7 sequential RPCs in `EditJobCard` or 2 serial RPCs in `ProgressTracker`) into **1 atomic server callable** executing under **1 `_get_current_user()` check and 1 `with db_cursor() as cursor:` checkout**.
   - Extract private `_fetch_*(cursor, ...)` helpers (never decorated with `@anvil.server.callable()`) so composite endpoints reuse the same cursor instead of calling other `@anvil.server.callable()` functions that re-authenticate and check out extra pool connections.
   - Replace correlated subqueries with flat `LEFT JOIN`s and compute totals/statuses in Python from already-fetched rows rather than running duplicate `SUM(...)` queries.
   - Encode small binary images (e.g., staff/customer signatures) as inline `data:image/png;base64,...` strings instead of `anvil.BlobMedia` so rendering does not trigger extra `/_/downlink-media/...` HTTP requests.

2. **Eliminate Click-Time Skulpt Construction via Multi-Tier Pre-Warming**:
   - **Speculative Search Warm**: After search results populate a selector dropdown, silently hydrate and pre-warm `result[0]` in `setTimeout(..., 0)` while the user opens the dropdown.
   - **Status-Prioritized Idle Pre-Warm**: Once bundle data is in RAM, pre-instantiate form components in `0 ms` `setTimeout` slices, starting with the modal matching the entity's current workflow stage. Defer second-level child pre-warms (e.g., `EditJobCard` inside `JobCardForm`) until the first modal's `show` event.
   - **Hover / Pointer-Down Pre-Warm**: Bind passive `pointerenter`, `mousedown`, and `touchstart` handlers on action buttons to immediately build that button's target form before `click` fires.
   - **In-Place Modal Swap**: Swap modal-to-modal transitions inside the existing open modal (`self.clear(); self.add_component(..., full_width_row=True)`) instead of closing and re-opening `alert()`.

3. **Zero Cache-Miss Windows (LRU + Non-Destructive Refresh)**:
   - Keep a bounded client LRU cache (e.g., 8 recent entities) evicted per `entity_id` on `window.bmaRealtime` events.
   - Never clear `_modals_cache` or `_prewarmed_modals` *before* an in-flight background refresh for the same entity returns; swap atomically when the response arrives.
   - Only invalidate caches when a modal closes with `value="updated"` (read-only closes return `False` and immediately re-prewarm that single modal).
   - Use server `cached_lookup()` + client `ModCache` (`ModGetData`) for reference lists (technicians, staff, locations, suppliers, parts), invalidated on mutations via `invalidate_lookup_cache()` + `publish_realtime_event()`.

4. **GPU Paint & Persistent Worker Rules**:
   - Avoid nested `backdrop-filter` blurs inside `.modal-content`, keep `.modal.fade` transitions disabled, avoid `body.modal-open` background flushes, and apply `contain: layout style;` to `.modal-dialog` / `.modal-content`.
   - Because `start-local.ps1` sets `DOWNLINK_CAN_PERSIST="true"`, always remind the user to **restart `anvil-app-server`** and **hard-refresh the browser (`Ctrl + Shift + R`)** to activate server-worker and CSS/client bundle optimizations.
