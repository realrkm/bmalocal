# BMALocal Unit Test Conventions & Harness Guide

This document outlines how unit tests are organized, mocked, and executed for BMALocal's server functions and business calculations.

---

## 1. Test Directory Structure
> **STRICT ISOLATION**: All unit tests, test fixtures, calculation helpers, and E2E browser tests must be placed inside the `tests/` folder. Production code (`server_code/BMALocal.py`) must never contain test functions or temporary test endpoints.

```text
tests/
├── conftest.py               # Shared pytest fixtures (mock DB, mock Anvil user, browser args)
├── helpers.py                # Test helper functions, calculation utilities, and stubs
├── unit/                     # Unit test suites (pytest)
│   ├── test_auth.py          # Session and role authorization checks
│   ├── test_jobcards.py      # JobCard status machines & validations
│   ├── test_invoices.py      # Invoice tax, line item, and total math
│   ├── test_walkietalkie.py  # Message formatting and chat helpers
│   └── test_contacts.py      # Client & technician record validations
├── integration/              # Integration tests against test schema
│   └── test_db_queries.py    # Query tests against isolated test schema
└── e2e/                      # End-to-End browser tests (Playwright)
    └── test_auth_flow.py     # Authentication, viewport rendering & regression flows
```

---

## 2. Mocking Anvil Runtime & Database Pool

Because BMALocal runs inside Anvil's server environment, tests executed outside Anvil (e.g. via `pytest`) mock the Anvil environment modules:

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_anvil_environment():
    """Mock anvil.users and database connection pool for pure unit tests."""
    with patch("anvil.users.get_user") as mock_get_user, \
         patch("server_code.BMALocal.get_db_connection") as mock_db_conn:
        mock_get_user.return_value = {
            "email": "admin@bmaauto.com",
            "role_id": 1,
            "role_name": "Admin"
        }
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db_conn.return_value = mock_conn
        yield {
            "get_user": mock_get_user,
            "cursor": mock_cursor,
            "conn": mock_conn,
        }
```

---

## 3. Standard Test Pattern for Callables

Every test suite must cover three fundamental branches:

```python
# Example: test_jobcards.py
import pytest
from server_code.BMALocal import update_job_card_status

def test_update_status_happy_path(mock_anvil_environment):
    """Admin updating valid status succeeds."""
    mock_cursor = mock_anvil_environment["cursor"]
    mock_cursor.rowcount = 1
    
    result = update_job_card_status(job_id=101, new_status="In-Service")
    assert result.get("success") is True

def test_update_status_unauthorized_role(mock_anvil_environment):
    """User without proper role is rejected."""
    mock_anvil_environment["get_user"].return_value = {
        "email": "guest@bmaauto.com",
        "role_id": 99,
        "role_name": "Guest"
    }
    with pytest.raises(Exception, match="permission"):
        update_job_card_status(job_id=101, new_status="In-Service")

def test_update_status_invalid_transition():
    """Transitioning to an invalid status raises a ValueError."""
    with pytest.raises(ValueError):
        update_job_card_status(job_id=101, new_status="NON_EXISTENT_STATUS")
```

---

## 4. Regression Test Catalog

When fixing a bug, register the regression test below:

| Bug ID / Summary | Offending File | Test Name | Guarded Scenario |
| :--- | :--- | :--- | :--- |
| **BUG-001**: Password toggle plain text leak | `theme/assets/password_toggle.js` | `test_password_toggle_no_logging` | Ensures DOM toggle never prints or dispatches password value |
| **BUG-002**: JobCard transition to In-Service missing technician | `server_code/BMALocal.py` | `test_jobcard_in_service_requires_tech` | Rejects transition if technician ID is null |
