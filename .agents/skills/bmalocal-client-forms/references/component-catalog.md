# BMALocal Component Catalog & Form Inventory

This document inventories the key forms, custom components, and navigation structures across BMALocal's 105+ client modules.

---

## 1. Core Workflow Forms

| Module / Form | Purpose | Key Components | Backing Server Callables |
| :--- | :--- | :--- | :--- |
| **`Main`** | Application shell, navigation drawer, status bar, user banner | `ColumnPanel`, `Link` (navigation items), `Button` (logout, walkie talkie) | `get_user_permissions`, `get_unread_notification_count` |
| **`JobCard` / `JobCardForm`** | Vehicle intake, symptom recording, inspection checklists, status flow | `TextBox` (VIN, Plate), `DropDown` (Make/Model, Tech), `RepeatingPanel` (checklist) | `get_jobcard_details`, `save_job_card`, `update_job_status` |
| **`Invoice` / `InvoiceForm`** | Billing, line items, VAT calculation, PDF generation | `DataGrid` (parts & labor), `Label` (totals), `Button` (Print/Download) | `generate_invoice`, `get_invoice_data`, `download_invoice_pdf` |
| **`Contacts` / `Client`** | Customer, supplier, and technician directory | `TextBox` (search), `RepeatingPanel` (contact cards), `Button` (Add/Edit) | `search_contacts`, `save_client_contact`, `get_client_history` |
| **`Booking`** | Workshop bay allocation & calendar | `Calendar`, `DropDown` (bays), `RepeatingPanel` (daily schedule) | `get_bookings`, `save_booking`, `cancel_booking` |
| **`Workflow`** | Vehicle repair pipeline, technician queues | `ColumnPanel` (kanban stages: Draft, In-Service, QC, Done) | `get_workflow_stages`, `move_workflow_stage` |
| **`ProgressTracker` / `ProgressTrackerMobileView`** | Real-time vehicle repair milestone display | Step progress indicator, status chips, timeline log | `get_vehicle_progress`, `get_progress_tracker_mobile` |
| **`Inventory` / `PartsHub`** | Stock levels, location mapping, price catalogue | `DataGrid` (stock list), `TextBox` (barcode search) | `get_stock_balance`, `update_stock_quantity`, `search_parts` |

---

## 2. Specialized Components

- **`SignatureComponent` / `SignatureForm`**:
  - Implements HTML5 canvas signature capture via [theme/assets/signature.js](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/assets/signature.js).
  - Encodes signature to Base64 PNG data URL before sending to server for PDF embedding.
- **`WalkieTalkieChat`**:
  - Integrates with the WebSocket chat daemon on port 8765 via [theme/assets/walkietalkie.js](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/assets/walkietalkie.js).
  - Handles push-to-talk audio streaming, text messaging, and read receipts.
- **`BarcodeVideoFrame`**:
  - WebRTC camera video feed capturing 1D/2D barcodes using [theme/assets/barcode.js](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/assets/barcode.js).
