# BMALocal Authentication & Authorization Architecture

This reference outlines the authentication mechanism, user role hierarchy, and permission gates in BMALocal.

---

## 1. Authentication Mechanism

- **Provider**: Built-in Anvil Users service (`anvil.users`).
- **Session Identification**: `anvil.users.get_user()` retrieves the current session record from the local Anvil Users table.
- **Password Security**: Passwords stored as salted `bcrypt` hashes. Plaintext passwords must never be stored, transmitted, or logged.

---

## 2. Role Hierarchy & Permissions Matrix

Roles are queried from MySQL table `tbl_roles` matching `user["role_id"]`:

| Role Name | Role ID | Scope & Capabilities |
| :--- | :---: | :--- |
| **Admin** | `1` | Complete system access: user accounts, system configuration, all Job Cards, Invoices, pricing overrides, deletion rights. |
| **Manager** | `2` | Workshop floor supervisor: approve quotes, reassign technicians, override job card status, view inventory & revenue reports. |
| **Technician** | `3` | Workshop technician: view assigned job cards, log defects, request spare parts, advance job status to 'Ready for QC'. |
| **Staff / Service Advisor** | `4` | Customer intake: create bookings, create new Job Cards, search and register clients. |
| **Cashier / Accounts** | `5` | Financial operations: generate invoices, record payments, print receipts. |

---

## 3. Enforcement Pattern in Server Code

```python
# Function with role gate in server_code/BMALocal.py:
def _require_role(*allowed_roles):
    user = _get_current_user()
    role_id = user["role_id"]
    with db_cursor() as cursor:
        cursor.execute("SELECT Roles FROM tbl_roles WHERE ID = %s", (role_id,))
        row = cursor.fetchone()
    role_name = row[0] if row else None
    if role_name not in allowed_roles:
        raise Exception("You do not have permission to perform this action.")
    return user
```

---

## 4. Session Timeout Policy

- Interactive web sessions expire after 120 minutes of inactivity.
- On session expiration, client forms catch authentication errors and redirect to the login screen.
