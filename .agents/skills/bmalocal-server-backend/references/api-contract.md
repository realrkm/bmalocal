# BMALocal Server API Contract & Endpoint Register

This register documents key `@anvil.server.callable` endpoints, their input/output contracts, required roles, calling forms, and test coverage status.

---

## 1. Core Endpoints Register

| Callable Function | Input Parameters | Output Shape | Required Roles | Called From (Form) | Unit Test | E2E Path |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| `get_faq_html` | `None` | `str` (HTML) | Any Authenticated | `FAQ` | [x] | [ ] |
| `get_chat_user_profile` | `None` | `dict` (email, role_name, initials) | Any Authenticated | `WalkieTalkieChat` | [x] | [x] |
| `get_chat_history` | `limit: int = 50` | `list[dict]` (messages) | Any Authenticated | `WalkieTalkieChat` | [x] | [x] |
| `save_job_card` | `data: dict` | `dict` (success, job_id) | `Admin`, `Manager`, `Staff` | `JobCardForm` | [x] | [x] |
| `update_job_status` | `job_id: int, status: str` | `dict` (success, status) | `Admin`, `Manager`, `Technician` | `JobCard`, `Workflow` | [x] | [x] |
| `get_jobcard_details` | `job_id: int` | `dict` (full vehicle & tasks) | Any Authenticated | `JobCard`, `TechnicianJobCardDetails` | [x] | [x] |
| `generate_invoice` | `invoice_data: dict` | `dict` (success, invoice_id) | `Admin`, `Manager`, `Cashier` | `InvoiceForm` | [x] | [x] |
| `download_invoice_pdf` | `invoice_id: int` | `anvil.Media` (PDF binary) | `Admin`, `Manager`, `Cashier` | `Invoice` | [x] | [x] |
| `search_contacts` | `keyword: str` | `list[dict]` (contacts) | Any Authenticated | `Contacts`, `Client` | [x] | [x] |
| `save_client_contact` | `contact_dict: dict` | `dict` (success, contact_id) | `Admin`, `Manager`, `Staff` | `EditClient` | [x] | [x] |
| `calculate_invoice_breakdown` | `subtotal: float, discount_percent: float = 0.0, tax_rate_percent: float = 16.0` | `dict` (subtotal, discount_amount, net_subtotal, tax_amount, total_amount) | Any Authenticated | `InvoiceForm`, `QuoteForm` | [x] | [ ] |
| `get_stats` | `user_agent_string: str` | `dict` (client geolocation/OS) | Public / Anvil context | `Launcher`, `Main` | [x] | [ ] |

---

## 2. Maintenance Rule

Whenever a new `@anvil.server.callable` is created or modified in `server_code/BMALocal.py`, update this table with its signature, role requirements, and test tracking checkboxes.
