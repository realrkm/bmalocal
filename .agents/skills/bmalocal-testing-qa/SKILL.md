---
name: bmalocal-testing-qa
description: >-
  Unit testing and Playwright end-to-end testing standards for BMALocal —
  what must be tested, how, and where. Use for EVERY code change before it is
  considered done: new/changed server callables, new/changed forms, schema
  changes, and bug fixes (regression test required).
---

# BMALocal Testing & Quality Assurance Standards

Quality and testing in BMALocal are non-negotiable parts of every change. No feature, refactoring, or bug fix is complete until verified by automated tests.

---

## 1. Golden Rule for Bug Fixes (Test First)

> **When a bug is reported, your first action MUST be to reproduce it as a failing unit test or Playwright E2E journey BEFORE touching implementation code.**
> Only once that test demonstrably fails for the exact root cause do you write the fix. The same test then guards against regression permanently. Skipping straight to code edits is treated as incomplete work.

---

## 2. Test Pyramid for BMALocal

```text
       /\
      /  \     End-to-End (Playwright) — Real user journeys across desktop & mobile viewports
     /----\    
    /      \   Integration Tests — Server callables executed against disposable test MySQL DB
   /--------\  
  /          \ Unit Tests (pytest/unittest) — Server calculations, auth validation, status machines
 /------------\
```

### 2.1 Unit Tests (Fast, Run on Every Change)
- **Scope**: Server-side business logic in [server_code/BMALocal.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/server_code/BMALocal.py) and [server_code/modAnalytics.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/server_code/modAnalytics.py).
- **Target**:
  1. Input validation & sanitization logic.
  2. Financial calculations (e.g. invoice line item totals, tax calculations, discounts).
  3. Status transition state machines (JobCard: Draft &rarr; In-Service &rarr; Ready for QC &rarr; Completed &rarr; Invoiced).
  4. Authentication & authorization rejections (unauthenticated or unprivileged users).
- **Conventions**: Documented in [references/unit-test-conventions.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/references/unit-test-conventions.md).

### 2.2 Integration Tests
- Verify SQL queries and transactions against an isolated test database (or SQLite in-memory / mock connection pool).
- Never run tests against the live production MySQL database (`bmaautoaccessories2017`).

### 2.3 End-to-End Tests (Playwright)
- **Location**: `.agents/skills/bmalocal-testing-qa/e2e/` (or project root `e2e/`).
- **Configuration**: [e2e/playwright.config.ts](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/e2e/playwright.config.ts) defines projects for Desktop Chromium, Tablet Viewport, and Mobile Viewport.
- **Coverage Catalog**: Maintained in [references/e2e-test-catalog.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/references/e2e-test-catalog.md).

---

## 3. Unit Testing Requirements for `@anvil.server.callable`

Every new or modified server callable must ship with tests covering:
1. **Happy Path**: Standard valid input returns the expected data structure and status code.
2. **Invalid Input Case**: Out-of-bounds numbers, missing required parameters, or invalid strings raise clear, handled exceptions.
3. **Unauthorized Caller Case**: Mutating calls verify that `_require_role()` raises an access denied exception when simulated with an unauthenticated or unauthorized role.
4. **Boundary Checks**: Calculation functions must test edge boundaries (e.g. `0` amount, negative quantities, max integers).

---

## 4. End-to-End Testing with Playwright

1. **Stable Selectors**: Target semantic labels, `automation_name`, or explicit data attributes. Avoid brittle generated CSS class names or positional DOM indices.
2. **Test Isolation**: Run against the application started in test mode (`start-local.ps1 -forTests`) with fixture data.
3. **Flakiness Policy**: Never use arbitrary `time.sleep()`. Use Playwright's auto-waiting assertions (e.g. `await expect(page.locator(...)).toBeVisible()`).
4. **Treat Failures as Regressions**: When an E2E test fails, diagnose and resolve the underlying defect instead of deleting or disabling the test.

---

## 5. Non-Negotiable Test Gate (Before Any Task is Done)

A change may only be marked complete when:
- [ ] All unit tests pass cleanly.
- [ ] Relevant Playwright E2E journey(s) pass on desktop and mobile viewports.
- [ ] [references/unit-test-conventions.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/references/unit-test-conventions.md) and [references/e2e-test-catalog.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/references/e2e-test-catalog.md) are updated.
- [ ] If fixing a bug, the regression test that reproduces the bug is committed.
