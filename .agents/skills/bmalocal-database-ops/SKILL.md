---
name: bmalocal-database-ops
description: >-
  MySQL schema, queries, migrations, and connection handling for BMALocal
  (Job Cards, Invoices, Contacts, Users tables). Use when adding/changing
  tables or columns, writing migrations, or any query touching the database.
---

# BMALocal Database Operations & Schema Management

This skill governs all MySQL database interactions, connection pooling, transactional operations, and schema migrations for the BMALocal database (`bmaautoaccessories2017`).

---

## 1. 100% Parameterized SQL (Hard Rule)

Every query executed via `mysql-connector-python` must use `%s` placeholders with parameters passed as a tuple. **String interpolation is strictly prohibited.**

```python
# FORBIDDEN (Vulnerable to SQL Injection and syntax errors):
cursor.execute(f"SELECT * FROM tbl_jobcarddetails WHERE ChassisNo = '{chassis}' AND Status = '{status}'")

# MANDATORY:
cursor.execute(
    "SELECT ID, ChassisNo, RegistrationNo, Status FROM tbl_jobcarddetails WHERE ChassisNo = %s AND Status = %s",
    (chassis, status)
)
```

---

## 2. Safe Connection Lifecycle & Pool Hygiene

All database access must use the `db_cursor()` context manager from [server_code/BMALocal.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/server_code/BMALocal.py#L88-L102):

```python
from server_code.BMALocal import db_cursor

with db_cursor() as cursor:
    cursor.execute("SELECT ID, ClientName FROM tbl_clientcontacts WHERE ID = %s", (client_id,))
    client = cursor.fetchone()
    # Transaction commits automatically on exit; rolls back on exception
```

- **Connection Pool**: Backed by `mysql.connector.pooling.MySQLConnectionPool(pool_name="bma_pool", pool_size=5)`.
- **Never hold connections open**: Perform DB operations promptly; never call network services (APIs, PDF generation) while holding a database cursor open.

---

## 3. Query Efficiency & Hot Paths

- **No `SELECT *`**: Always select specific columns. Tables like `tbl_jobcarddetails` (32 columns, 11k+ rows) and `tbl_invoices` contain dozens of columns; querying only what's needed saves RAM and network serialization overhead.
- **Index Verification**: Any query filtering on `RegNo`, `ChassisNo`, `JobCardRef`, `Status`, or `ClientDetails` must match an existing index in [references/schema.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-database-ops/references/schema.md).
- **Batch Processing**: Use `cursor.executemany()` for multi-row insertions (e.g. invoice line items, stock count entries).

---

## 4. Schema Migrations Checklist

Follow the safe migration protocol in [references/migration-checklist.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-database-ops/references/migration-checklist.md) whenever altering tables:
1. Backup database with `mysqldump`.
2. Write reversible SQL migration script.
3. Test migration on a staging copy.
4. Apply to target database.
5. Update [references/schema.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-database-ops/references/schema.md).
6. Run unit and E2E tests.

---

## 5. Mandatory Completion Gate

Before marking any database change complete:
1. Verify query parameterization against [bmalocal-security](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-security/SKILL.md).
2. Confirm no leaked connections or unclosed cursors per [bmalocal-performance-reliability](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-performance-reliability/SKILL.md).
3. Ensure affected unit and integration tests pass per [bmalocal-testing-qa](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/SKILL.md).
