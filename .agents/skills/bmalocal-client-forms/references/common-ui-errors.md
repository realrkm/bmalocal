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
