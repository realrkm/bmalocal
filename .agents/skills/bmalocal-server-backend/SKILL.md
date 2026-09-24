---
name: bmalocal-server-backend
description: >-
  Anvil server modules: @anvil.server.callable functions, authentication,
  session handling, and business-rule validation for BMALocal. Use when
  adding/modifying RPC endpoints, user permissions, Job Card/Invoice/Contact
  business logic, or anything under server_code/.
---

# BMALocal Server Backend Development

This skill governs all backend business logic, `@anvil.server.callable` endpoints, authentication checks, role permissions, and transaction handling in [server_code/BMALocal.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/server_code/BMALocal.py) and [server_code/modAnalytics.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/server_code/modAnalytics.py).

---

## 1. RPC Contract & Function Conventions

Every `@anvil.server.callable` function must follow this structure:

```python
@anvil.server.callable()
def update_job_status(job_id, new_status, notes=None):
    """
    Update JobCard status with state validation and audit logging.
    
    Args:
        job_id (int): Primary key in tbl_jobcarddetails.
        new_status (str): Target status string.
        notes (str, optional): Status change remark.
    Returns:
        dict: {"success": bool, "job_id": int, "status": str, "updated_at": str}
    """
    # 1. AuthZ Gate
    user = _require_role("Admin", "Manager", "Technician")
    
    # 2. Input Validation
    if not isinstance(job_id, int) or job_id <= 0:
        raise ValueError("Invalid job_id provided.")
    allowed_statuses = {"Draft", "In-Service", "Ready for QC", "Completed", "Invoiced", "Cancelled"}
    if new_status not in allowed_statuses:
        raise ValueError(f"Status '{new_status}' is not a valid status.")

    # 3. Database Execution within context manager
    with db_cursor() as cursor:
        cursor.execute(
            "UPDATE tbl_jobcarddetails SET Status = %s, UpdatedAt = CURRENT_TIMESTAMP WHERE ID = %s",
            (new_status, job_id)
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Job Card #{job_id} not found.")

    return {
        "success": True,
        "job_id": job_id,
        "status": new_status,
        "updated_at": datetime.datetime.now().isoformat(),
    }
```

### Key Principles
- **Explicit Parameters**: Define arguments clearly; avoid `**kwargs` for public RPC contracts unless forwarding.
- **Return Shape**: Return explicit JSON-serializable dictionaries or lists with a consistent structure (`{"success": True, ...}`).
- **No Bare `except:`**: Catch specific exceptions (`ValueError`, `mysql.connector.Error`).
- **Sanitized Logging**: Log errors with context to [logs/service_output.log](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/logs/service_output.log); never log customer passwords or payment tokens.

---

## 2. Authorization & Role Verification

1. **Mandatory Identity Verification**:
   - Every protected function must call `_get_current_user()` or `_require_role(*allowed_roles)` at the very beginning.
   - Client-side permission checks are purely visual; the server is the sole authority.
2. **Role Mapping in MySQL**:
   - Roles are looked up from `tbl_roles` via `role_id` on the logged-in user record.
   - Standard roles: `Admin`, `Manager`, `Technician`, `Staff`, `Cashier`.
   - See [references/auth-and-permissions.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-server-backend/references/auth-and-permissions.md).

---

## 3. Server-Side Validation (True Gate)

Server validation mirrors and enforces all business constraints:
- **Job Cards**: Reject status updates if mandatory inspection points are unverified or technician is unassigned.
- **Invoices**: Enforce line item calculation integrity server-side (`total = sum(qty * price) + vat - discount`). Never trust totals calculated solely on the client.
- **Contacts**: Reject invalid phone formats, duplicate primary contacts, or malformed email addresses.

---

## 4. Unit Test Obligation

- **Every new or updated callable MUST ship with a unit test** in `tests/unit/` created or updated in the same commit.
- A callable is not done without test coverage proving:
  1. Happy path return data.
  2. Rejection of invalid inputs.
  3. Rejection of unauthorized users.
- Register all endpoints and their test status in [references/api-contract.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-server-backend/references/api-contract.md).

---

## 5. Security & Test Gate

Before marking any backend change complete:
1. Verify against the [bmalocal-security](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-security/SKILL.md) checklist (parameterized queries, role check, no secret leaks).
2. Run pytest to confirm all unit tests pass per [bmalocal-testing-qa](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/SKILL.md).
3. If fixing a reported bug, verify the regression test was written first and now passes.
