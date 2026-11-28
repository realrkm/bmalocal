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
  - [client_code/ModCache.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/ModCache.py) for TTL client caching with automatic WebSocket topic invalidation.
  - [client_code/WalkieTalkieChat.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/WalkieTalkieChat.py) for realtime chat integration.

---

## 2. Standard Form Patterns

1. **Component Initialization**:
   - Always call `self.init_components(**properties)` as the first line in `__init__`.
   - Do **not** call `anvil.js.call('replaceBanner')` inside modal forms (`alert()` content) or reusable subcomponents (`SearchKeyword`); banner suppression is handled globally by CSS and top-level shell forms.
2. **Server Calls**:
   - **Never fire multiple sequential `anvil.server.call` / `call_s` round-trips inside `__init__` or `populateForm`**. Pass preloaded data into the form constructor or fetch a single bundled bootstrap dictionary.
   - Use `anvil.server.call_s()` with `with anvil.server.no_loading_indicator:` for silent background prefetches/revalidations where failure does not block the UI.
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

## 2A. Instant Form & Modal Loading Architecture (`< 16 ms` Target)

Reference implementations: [ProgressTracker/\_\_init\_\_.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/ProgressTracker/__init__.py), [JobCardForm/\_\_init\_\_.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/JobCardForm/__init__.py), and [EditJobCard/\_\_init\_\_.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/EditJobCard/__init__.py).

Whenever building or optimizing forms, modals, or multi-tab hubs, eliminate **all** click-time RPCs, synchronous Skulpt component construction, cache-miss race windows, and GPU paint bottlenecks:

1. **Atomic Single-RPC Hydration (Eliminate Two-RPC Race Windows)**:
   - When selecting an entity on a parent screen (e.g., selecting a Job Card in `ProgressTracker`), fetch **both** the parent summary and child modal payloads in **one atomic RPC** (e.g., `get_progress_tracker_data(job_id, include_modals=True)`).
   - Never wait for RPC #1 to render the UI and then start RPC #2 in the background for button payloads — clicking a button while RPC #2 is in flight causes a cache miss and queues behind RPC #2.
   - Where a search precedes dropdown selection (`btn_SearchCustomer_click`), **speculatively warm `result[0]`** in `setTimeout(..., 0)` while the user opens the dropdown.

2. **Idle Pre-Warming + Hover/Pointer Pre-Warming of Form Instances**:
   - Even with cached JSON data, constructing 35–60 Anvil components in Skulpt (`DatePicker`, `DataGrid`, `RepeatingPanel` row templates, `SignatureForm`) takes `150–400 ms` if run synchronously on `click`.
   - **Staggered Idle Pre-Warm**: As soon as modal data arrives, pre-instantiate non-empty modal forms in detached DOM memory via `setTimeout(..., 0)` slices, ordered with the active workflow status's modal **first**. Defer nested second-level pre-warms (e.g., `JobCardForm(prewarm_edit=False)` only pre-warming `EditJobCard` on its `show` event).
   - **Hover / Pointer-Down Pre-Warm**: Attach passive `pointerenter`, `mousedown`, and `touchstart` listeners on modal trigger buttons to immediately build that button's form (`80–250 ms` before `click` fires).
   - **Read-Only Close Preservation**: Return `value="updated"` from `x-close-alert` **only** when data actually mutated (`value=False` on read-only close). On `False`, keep `_modals_cache` intact and immediately re-prewarm that single modal at `setTimeout(..., 0)`. On `"updated"`, atomically refresh via `refresh_selected_job_card(force_server=True)` — never clear `_modals_cache` without refilling it.

3. **In-Place Modal Swapping (Never Close + Re-open `alert()`)**:
   - Transitioning from one modal to another via `self.btn_Close_click()` followed by `alert(content=NextForm(...))` triggers two full modal transitions, tears down the backdrop, and **prematurely resumes the caller's post-`alert()` code**.
   - Instead, swap inside the already-open modal container and forward `x-close-alert`:
     ```python
     edit_form = self._prewarmed_edit_form or EditJobCard(jobcard_data=self.form_data)
     edit_form.set_event_handler(
         "x-close-alert",
         lambda **e: self.raise_event("x-close-alert", value=e.get("value", False)),
     )
     self.clear()
     self.add_component(edit_form, full_width_row=True)
     ```

4. **Non-Destructive Realtime Refresh & Multi-Entity LRU Cache**:
   - Maintain a bounded LRU cache (e.g., last 8 entities) mapping `entity_id -> {summary, modals, prewarmed_forms}`, selectively evicted by `entity_id` on `window.bmaRealtime` events, so switching back to a recent item takes `0 ms` and `0 RPCs`.
   - When refreshing the **same** currently selected entity (via WebSocket event or fallback timer), **keep the existing `_modals_cache` and `_prewarmed_modals` active while the RPC is in flight** and swap atomically on completion — never wipe the cache upfront.

5. **Lazy Subform Imports, Cached Reference Lookups & Stale-Load Guards**:
   - Import subforms lazily inside button/dropdown handlers (`Contacts`, `Settings`, `PartsHub`, `Report`, `DefectsForm` secondary dialogs) rather than at module top-level.
   - Always back `SearchKeyword` / dropdown reference lists with `ModGetData` (`ModCache` + realtime invalidation), e.g., `ModGetData.getTechniciansCached()` and `ModGetData.getStaffCached()`.
   - Guard rapid tab/report switching with a monotonic sequence counter (`self._load_seq += 1`) so slow views never overwrite newer user selections.

6. **Modal CSS, GPU Compositing & Asset Preloading**:
   - **No Nested `backdrop-filter`**: `.modal-content` already applies `backdrop-filter: blur(28px)`. Inner `.modal-content .anvil-role-glass-panel` cards must keep `backdrop-filter: none !important` to avoid 9–10x stacked GPU Gaussian blur passes.
   - **Instant Modal Paint & Layout Containment**: Keep `.modal.fade` transitions disabled (`transition: none !important`), use `contain: layout style;` on `.modal-dialog` and `.modal-content` so mounting `DataGrid` rows never reflows the underlying page, avoid `body.modal-open` background flushes, and preload static modal images (`new Image().src = ...`) once at startup.
   - **Inline Base64 for Small Dynamic Images**: Pass small DB images (like signatures) as `data:image/png;base64,...` strings rather than `anvil.BlobMedia` inside bundled payloads to avoid secondary `/_/downlink-media/...` HTTP fetches on render.

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
- **Test Selectors**: Every interactive element (inputs, buttons, tabs) must have a stable text label, accessible name, or `automation_name` for Playwright tests (see [bmalocal-testing-qa](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/SKILL.md)). Check `tests/e2e/` before renaming critical components.

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
