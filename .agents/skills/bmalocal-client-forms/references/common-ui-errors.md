# BMALocal Common UI Errors & Solutions

This reference catalogs recurring client-side UI bugs, symptoms, root causes, and verified fix patterns.

---

## 1. Password Visibility Toggle Desynchronization

- **Symptom**: Clicking the eye icon fails to toggle password visibility or resets the input focus.
- **Root Cause**: Anvil re-renders the DOM wrapper on component property updates, detaching event listeners bound by `password_toggle.js`.
- **Fix Pattern**: Use event delegation on a stable parent container or re-initialize `window.initPasswordToggles()` in the form's `form_show` event callback. Ensure no raw password strings are logged or stored.

---

## 2. Horizontal Scroll on Mobile Viewports

- **Symptom**: On screen widths below `600px`, the page exhibits horizontal overflow scrolling.
- **Root Cause**: Hardcoded pixel widths on `ColumnPanel` slots (e.g. `width: 320px`), or data table columns with inflexible min-widths.
- **Fix Pattern**: Set `col_widths: {}` in `form_template.yaml` for small screens, allow text wrapping, or switch to dedicated card repeating panels (like `ProgressTrackerMobileView`).

---

## 3. Double-Click Duplicate Submission

- **Symptom**: Fast double-clicking "Save Job Card" or "Generate Invoice" creates duplicate records in MySQL.
- **Root Cause**: Submit button remained enabled while the first `anvil.server.call()` was awaiting network response.
- **Fix Pattern**:
  ```python
  def btn_save_click(self, **event_args):
      self.btn_save.enabled = False
      try:
          anvil.server.call("save_job_card", self.get_form_data())
      finally:
          self.btn_save.enabled = True
  ```

---

## 4. Canvas Signature Scaling on High-DPI Screens

- **Symptom**: Customer signature looks blurry or coordinates offset from the touch/pen position.
- **Root Cause**: Canvas internal pixel resolution does not match CSS display width/height when `window.devicePixelRatio > 1`.
- **Fix Pattern**: In `signature.js`, multiply canvas width and height by `window.devicePixelRatio` and scale the 2D rendering context accordingly.

---

## 5. Slow or Intermittently Sluggish Modal & Form Loading (`200–1,000 ms` Lag)

- **Symptom**: Clicking a modal button (e.g., `EditJobCard` or Progress Tracker's `JOBCARD`, `DEFECTS`, `QUOTE`, `CONFIRM`, `INVOICE`, `PAYMENT`) freezes briefly before appearing, or opens instantly sometimes and lags on other clicks.
- **Root Causes**:
  1. **Sequential RPCs in `__init__` / `populateForm`**: Firing 3–7 synchronous `anvil.server.call` / `call_s` calls before the form renders.
  2. **Click-Time Skulpt Component Construction**: Calling `FormClass(...)` synchronously inside a click handler when the form contains 35–60 Anvil components (`DatePicker`, `DataGrid` + `RepeatingPanel` row templates, `SignatureForm`, `SearchKeyword`).
  3. **Two-RPC Dropdown Race Window**: Fetching summary data in RPC #1 and modal payloads in a background RPC #2 — clicking a button while RPC #2 is in flight misses cache and queues behind RPC #2.
  4. **Destructive Cache Invalidations**: Clearing `_modals_cache` *before* a background WebSocket refresh returns, invalidating cache on read-only modal closes, or calling `_invalidate_modals_cache()` *after* a child edit form already refreshed the parent tracker.
  5. **Double `alert()` Modal Transitions & GPU Blur Stacking**: Closing one `alert()` and opening a second `alert()`, animating `.modal.fade` over `backdrop-filter: blur(28px)`, nesting `.anvil-role-glass-panel` `backdrop-filter` blurs inside `.modal-content`, flushing `body.modal-open` backgrounds, or using `anvil.BlobMedia` for small signature images (which triggers a lazy `/_/downlink-media/...` HTTP request on render).
- **Verified Fix Pattern** (see [ProgressTracker/\_\_init\_\_.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/ProgressTracker/__init__.py), [JobCardForm/\_\_init\_\_.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/JobCardForm/__init__.py), [EditJobCard/\_\_init\_\_.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/EditJobCard/__init__.py)):
  - Bundle parent summary + child modal data into **one single-cursor server RPC** (`include_modals=True`), encoding small images as inline `data:image/png;base64,...` strings.
  - Pre-warm modal component instances in `0 ms` `setTimeout` slices (prioritized by workflow status) **plus** `pointerenter`/`mousedown`/`touchstart` hover listeners on trigger buttons, backed by an 8-item LRU cache and speculative warming on top search hits.
  - Swap modal-to-modal views **in-place** (`self.clear(); self.add_component(next_form, full_width_row=True)`) and only invalidate caches when `x-close-alert` returns `"updated"`.
  - Keep `.modal-content .anvil-role-glass-panel { backdrop-filter: none !important; }`, `.modal.fade { transition: none !important; }`, and `contain: layout style;` on `.modal-dialog` / `.modal-content`.
