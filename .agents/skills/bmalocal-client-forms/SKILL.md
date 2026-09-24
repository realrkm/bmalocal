---
name: bmalocal-client-forms
description: >-
  Anvil client-side UI: forms, components, data bindings, event handlers, and
  YAML layout definitions for BMALocal. Use when creating/editing forms under
  client_code/, changing form_template.yaml, fixing input validation, adding
  UI components, or touching theme.css.
---

# BMALocal Client Forms Development

This skill governs all client-side Anvil UI components, form templates, user interactions, and event handlers in BMALocal.

---

## 1. Directory Structure Conventions

- Every form lives under its own module directory: `client_code/<ModuleName>/`
- Each form consists of two essential files:
  - `__init__.py`: Python controller containing component initialization, event callbacks, and local UI state.
  - `form_template.yaml`: Anvil layout schema defining component hierarchies, properties, and data bindings.
- Shared client utilities and navigation helpers:
  - [client_code/ModNavigation](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/ModNavigation) for routing between views.
  - [client_code/ModGetData.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/ModGetData.py) for common client data lookups.
  - [client_code/WalkieTalkieChat.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/WalkieTalkieChat.py) for realtime chat integration.

---

## 2. Standard Form Patterns

1. **Component Initialization**:
   - Always call `self.init_components(**properties)` as the first line in `__init__`.
2. **Server Calls**:
   - Use `anvil.server.call_s()` for silent/background requests where failure does not block the UI.
   - For primary user actions, wrap `anvil.server.call()` in error handling:
     ```python
     try:
         result = anvil.server.call("save_job_card", data)
     except anvil.server.AppOfflineError:
         anvil.Notification("Local server offline. Please verify connection.", style="danger").show()
     except Exception as e:
         anvil.Notification(str(e), style="warning").show()
     ```
3. **State Management**:
   - Store state in explicit Python instance attributes (`self.job_id`, `self.current_step`), never by reading text or properties off visual DOM components.
4. **In-Flight UI Feedback**:
   - Disable submission buttons while requests are in flight to prevent duplicate submissions.

---

## 3. Client Validation Rules (UX Feedback Only)

Client validation provides immediate user feedback, but is **never a security boundary**; all rules must be validated server-side (see [bmalocal-security](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-security/SKILL.md)).

- **Job Card**: Requires `RegNo` / `RegistrationNo` (or `ChassisNo`), `ClientName` (mapped to `ClientDetails`), `ContactPhone`, and at least one logged symptom or task description.
- **Invoice**: Requires valid `JobCardID` (mapped to `AssignedJobID`), client reference, at least one line item with `quantity > 0` and `unit_price >= 0`, and positive payment/subtotal.
- **Contact**: Requires `ClientName`, `PhoneNumber` (valid format), and `Email` (if provided, must match email regex).

---

## 4. Theming, Styles & Dark Mode

- Pull design tokens strictly from [theme/parameters.yaml](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/parameters.yaml) and [theme/assets/theme.css](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/assets/theme.css).
- Assign standard roles: `card`, `primary-color`, `secondary-color`, `headline`, `subheading`.
- Dark/light mode uses the project's CSS class/variable approach. Do not introduce incompatible third-party themes.

---

## 5. Responsiveness & Testability Hooks

- **Responsive Design**: Follow breakpoint guidelines in [bmalocal-ui-ux-responsive](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-ui-ux-responsive/SKILL.md). Never hardcode pixel widths.
- **Test Selectors**: Every interactive element (inputs, buttons, tabs) must have a stable text label, accessible name, or `automation_name` for Playwright tests (see [bmalocal-testing-qa](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/SKILL.md)). Check `e2e/` before renaming critical components.

---

## 6. Common UI Errors & Solutions

Refer to [references/common-ui-errors.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-client-forms/references/common-ui-errors.md) for known root causes and fixes (e.g. password visibility toggle, signature pad sizing).

---

## 7. Mandatory Completion Gate

No client-form change is considered done until:
1. **Bug-First Check**: If fixing a bug, a reproducing test was written first per [bmalocal-testing-qa](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/SKILL.md).
2. **Responsive Verification**: The form renders cleanly without horizontal scroll on Desktop (`1440px`), Tablet (`768px`), and Mobile (`375px`).
3. **Security Check**: Confirm all inputs are also validated on the server per [bmalocal-security](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-security/SKILL.md).
4. **Test Pass**: Relevant Playwright E2E journey passes.
