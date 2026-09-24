---
name: bmalocal-security
description: >-
  Security standards for BMALocal covering authentication, input validation,
  SQL injection prevention, secrets handling, and transport security. Use for
  ANY change to server_code/, database queries, auth flows, file uploads, or
  before merging any feature — not just security-labeled tasks.
---

# BMALocal Security Standards & Checklist

This skill defines non-negotiable security requirements for all BMALocal modifications. Every code change touching server logic, database interactions, user authentication, or data transport must be verified against this checklist.

---

## 1. Authentication & Sessions

- [ ] **Server-Side Session Validation**: Every `@anvil.server.callable` that is not explicitly public MUST begin by calling `_get_current_user()` from [server_code/BMALocal.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/server_code/BMALocal.py#L66-L72). Never trust client-side claims of identity or session state.
- [ ] **Role Validation**: All privileged or mutating operations must call `_require_role(*allowed_roles)` inside the function body. Client-side visibility flags (e.g. `self.btn_edit.visible = False`) are UX conveniences only, never authorization barriers.
- [ ] **Password Storage**: Passwords must always be hashed with `bcrypt` using salted hashes (`bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())`). Plaintext passwords must NEVER be saved to MySQL or printed in server/client logs.
- [ ] **Password Visibility Affordances**: The client-side toggle in [password_toggle.js](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/assets/password_toggle.js) is strictly a local DOM rendering switch (`type="text"` vs `type="password"`). It must never transmit, log, or persist raw passwords outside the standard login/reset flows.
- [ ] **Session Expiry**: Inactive sessions must terminate per the session policy. Do not extend sessions indefinitely in memory.

---

## 2. Authorization & Privilege Gates

- [ ] **Server-Side Role Checks**: Role validation queries `tbl_roles` by `ID = %s` using the logged-in user's `role_id`.
- [ ] **Ownership Verification**: For customer/technician-specific views (e.g. assigned job cards, invoices), verify that the requesting user's ID matches the record owner or that the user has `Admin`/`Manager` privileges.

---

## 3. Input Validation & SQL Injection Prevention

- [ ] **100% Parameterized SQL**: NEVER use Python f-strings, `+` string concatenation, or `.format()` when building SQL statements.
  - **Forbidden**: `cursor.execute(f"SELECT * FROM tbl_jobcarddetails WHERE ChassisNo = '{chassis}'")`
  - **Mandatory**: `cursor.execute("SELECT * FROM tbl_jobcarddetails WHERE ChassisNo = %s", (chassis,))`
- [ ] **Server-Side Validation**: Validate all incoming parameters (type, maximum string length, regex format, value ranges) in the server callable regardless of client-side checks.
- [ ] **File & Media Uploads**:
  - Validate MIME types, extension whitelists, and maximum file sizes server-side before persisting (e.g. signatures, invoices, job card attachments).
  - Sanitize all file names. Never use raw client-supplied file names directly in file system paths or download headers.

---

## 4. Secrets Management & Environment Hygiene

- [ ] **No Hardcoded Credentials**: Database passwords, encryption keys, and internal API secrets must reside exclusively in [.env](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.env) and be accessed via `os.getenv()`.
- [ ] **Git Exclusion**: Verify [.gitignore](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.gitignore) actively excludes `.env`, certificate private keys (`cert/*-key.pem`), and local database dumps.
- [ ] **Safe Defaults**: If an environment variable is missing, fail safely or default to a secure closed state rather than an open bypass.

---

## 5. Transport Security & Network Isolation

- [ ] **HTTPS for Web Traffic**: Production and LAN instances must run with TLS enabled via `--manual-cert-file` and `--manual-cert-key-file` per [bmalocal-service-runner](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-service-runner/SKILL.md).
- [ ] **Secure WebSockets (WSS)**: The Walkie-Talkie WebSocket server must use `wss://` with valid certificates when BMALocal runs on LAN over HTTPS. Unencrypted `ws://` connections fail under browser mixed-content policies.
- [ ] **Certificate Auditing**: Ensure certificates in `cert/` are valid and not expired before launching services.

---

## 6. Logging, Errors & Safe Information Disclosure

- [ ] **Sanitized Logs**: Never log passwords, authorization tokens, full credit card/payment details, or customer personal identification numbers to `logs/` or console output.
- [ ] **Generic Client Errors**: Exceptions caught in `@anvil.server.callable` functions should return user-friendly, non-technical error messages to the client. Detailed stack traces must only be logged to [logs/service_output.log](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/logs/service_output.log).

---

## 7. Security Testing & Pre-Merge Gate

- [ ] **Role Rejection Tests**: For any privileged callable, write a unit test proving that a caller with an invalid or insufficient role is rejected with an exception (see [bmalocal-testing-qa](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/SKILL.md)).
- [ ] **Pre-Merge Review**: No change touching `server_code/`, database queries, or authentication may be merged without completing this checklist.
