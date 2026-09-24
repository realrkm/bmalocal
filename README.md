# BMALocal - Automotive Workshop & Garage Management System

**BMALocal** is a comprehensive, production-grade automotive garage and workshop ERP application built for local and networked workshop environments. Designed specifically for specialized European vehicle repair centers (BMW, Mercedes-Benz, Audi, and general automotive workshops), it streamlines the entire lifecycle of workshop operations—from customer intake and digital job cards to real-time technician workflow tracking, stock inventory control, billing/invoicing, digital signature sign-offs, and live team communication.

---

## Table of Contents

- [Overview & Capabilities](#overview--capabilities)
- [Key Features & Modules](#key-features--modules)
- [Technology Stack](#technology-stack)
- [Prerequisites & System Requirements](#prerequisites--system-requirements)
- [Installation & Offline Setup Guide](#installation--offline-setup-guide)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Configure Python Virtual Environment (`venv` or `uv`)](#2-configure-python-virtual-environment-venv-or-uv)
  - [3. Install Python Dependencies (`pip` or `uv`)](#3-install-python-dependencies-pip-or-uv)
  - [4. Install External Tools (MySQL, Java, wkhtmltopdf)](#4-install-external-tools-mysql-java-wkhtmltopdf)
  - [5. Environment Configuration (.env)](#5-environment-configuration-env)
  - [6. SSL/TLS Certificate Setup (for HTTPS & WSS)](#6-ssltls-certificate-setup-for-https--wss)
- [Running the Application](#running-the-application)
  - [Starting the Anvil App Server](#starting-the-anvil-app-server)
  - [Starting the Walkie Talkie WebSocket Server](#starting-the-walkie-talkie-websocket-server)
  - [Unified Windows Launcher (.bat)](#unified-windows-launcher-bat)
- [Environment Variables Reference](#environment-variables-reference)
- [Project Directory Structure](#project-directory-structure)
- [Maintenance & Troubleshooting](#maintenance--troubleshooting)

---

## Overview & Capabilities

BMALocal is hosted locally via the open-source **Anvil App Server** coupled with a dedicated **MySQL** transactional database and an asynchronous Python **WebSocket Server**. It allows workshop teams to run the application completely offline on a local machine or across a Local Area Network (LAN) without relying on external cloud subscriptions.

---

## Key Features & Modules

### 1. Digital Job Cards (`JobCard`)
- Full vehicle identification logging (Chassis/VIN, Make, Model, License Plate, Mileage).
- Customer concern intake, symptom logging, and technician assignment.
- Multi-checkpoint workshop inspection checklists.
- Transition pipeline: Draft &rarr; In-Service &rarr; Ready for Quality Check &rarr; Released.

### 2. Client & Contact Directory (`Contacts`)
- Centralized database for Clients, Technicians, Staff, and Suppliers.
- Quick search by name, vehicle registration number, phone, or email.
- Complete vehicle service history per client.

### 3. Booking & Bay Scheduling (`Booking`)
- Workshop appointment scheduling and service bay allocation.
- Calendar view of pending, scheduled, and completed bookings.

### 4. Technician Workflow & Repair Prioritization (`Workflow`)
- Interactive vehicle repair staging pipeline.
- Task verification, defect documentation, and requested spare parts tracking.
- Technician portal with individual job queues and repair checklists.

### 5. Visual Progress Tracker (`ProgressTracker` & `ProgressTrackerMobileView`)
- Real-time visual progress milestone display from check-in to handover.
- Dedicated mobile view optimized for smartphone screens and workshop floor tablets.

### 6. Auto-Parts Inventory & Stock Control (`Inventory`)
- Multi-location warehouse tracking (shelf, bin, and rack mapping).
- Stock level monitoring with low-stock warnings and re-order thresholds.
- Stocktaking analysis, cycle counting guidelines, and inventory reconciliation tools.
- Barcode mapping and scanning via camera or handheld USB barcode scanners.

### 7. Parts Hub & Pricing Management (`PartsHub`)
- Buying vs. selling price catalogues and gross margin analysis.
- Supplier-to-part cross-referencing and brand comparison tools.
- Missing buying/selling price detection and automated pricing alerts.

### 8. Billing, Payments & Quotes (`Payment`, `Quote`, `InvoiceForm`)
- Generation of Interim Quotations, Confirmed Quotes, and Final Invoices.
- Invoice amendments and adjustment tracking.
- Partial, periodic, and full payment recording with balance tracking.
- One-click PDF generation for customer invoices and signed job cards via `wkhtmltopdf`.

### 9. Digital Customer Signatures (`SignatureComponent`)
- Touchscreen, stylus, or mouse signature capture on job cards and collection forms.
- Embedded signature image rendering directly onto generated PDF documents.

### 10. Walkie Talkie Real-Time Chat (`WalkieTalkieChat`)
- **Instant Messaging**: Real-time asynchronous communication across all workshop users.
- **Persistent Floating Action Button (FAB)**: Accessible in the lower-right corner across all application sections.
- **Pulsing Unread Badge**: Displays real-time unread count and blinks when new messages arrive.
- **Message Editing**: Allows senders to edit their sent messages within 15 minutes of transmission, updating all connected screens instantly with an `edited` audit indicator.
- **Online Presence**: Displays active online member counts and logged-in user names.
- **Encrypted WSS**: Natively supports TLS encryption (`wss://`) to comply with browser Mixed Content security when accessed over HTTPS.

### 11. Role-Based Access Control (RBAC) & Security (`Roles`, `Settings`)
- Multi-level role hierarchy (Administrator, Accounts, Service Advisor, Technician, Staff).
- Fine-grained permission controls per navigation section and sub-action.
- Session authentication with secure password hashing.

---

## Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Application Server** | `anvil-app-server` (v1.17+) | Open-source Python web app server by Anvil Works |
| **Frontend Framework** | Anvil Client (Python Skulpt) | Pure Python client logic compiling to browser JavaScript |
| **Frontend Styling** | Vanilla CSS3 (`theme.css`) | Responsive design, glassmorphism UI, fixed FAB controls |
| **Frontend Scripts** | Native JavaScript | `walkietalkie.js`, `signature.js`, `selfservice.js`, `barcode.js` |
| **Chat Server** | `websockets` (v17+) | Asynchronous real-time WebSocket server integrated into `BMALocal.py` |
| **Primary Database** | MySQL 8.0+ / MariaDB | Relational storage for business entities and chat history |
| **Internal Data Store** | PostgreSQL (embedded) | Embedded DB managed by Anvil App Server for app state/users |
| **Document Engine** | `wkhtmltopdf` + `pdfkit` | Headless HTML-to-PDF rendering for invoices and reports |
| **Spreadsheets** | `openpyxl` | Excel report exporting |
| **Environment** | `python-dotenv` | Strict configuration management via `.env` file |

---

## Prerequisites & System Requirements

Before setting up BMALocal on any target machine, ensure the following software is installed:

1. **Operating System**: Windows 10/11 (64-bit), Windows Server 2016+, or modern Linux (Ubuntu 20.04+ / Debian 11+).
2. **Python**: Python **3.10** to **3.14** (64-bit). Ensure `python` and `pip` are added to your system `PATH`.
3. **Java Runtime (JRE/JDK)**: Java 11, 17, or 21 (64-bit) is **required** by `anvil-app-server`.
4. **MySQL Database**: MySQL Server 8.0+ or MariaDB 10.5+ running locally or reachable over the local network.
5. **wkhtmltopdf**: Version 0.12.6+ with patched Qt for invoice/job card PDF generation.
6. **Git**: Git for Windows or Linux to pull and update source code.

---

## Installation & Offline Setup Guide

### 1. Clone the Repository

Clone the project repository to your desired directory:
```bash
git clone https://github.com/realrkm/bmalocal.git BMALocal
cd BMALocal
```

### 2. Configure Python Virtual Environment (`venv` or `uv`)

To prevent dependency conflicts and ensure reproducible offline operation, you should run BMALocal inside an isolated virtual environment. You can use standard Python **`venv`** or the ultra-fast modern **`uv`** package manager.

#### Option A: Standard Python `venv` (Built into Python)

1. **Create the virtual environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
     *(If script execution is disabled on your system, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first)*
   - **Windows (Command Prompt / CMD)**:
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

3. **Verify activation**:
   Your terminal prompt should now display `(venv)`.

---

#### Option B: Modern High-Performance `uv` (Recommended for Speed)

[`uv`](https://github.com/astral-sh/uv) is an extremely fast Python package and environment manager written in Rust (10-100x faster than standard `pip`).

1. **Install `uv` (if not already installed)**:
   - **Windows (PowerShell)**:
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - **Linux / macOS**:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - **Via standard pip (any OS)**:
     ```bash
     pip install uv
     ```

2. **Create the virtual environment with `uv`**:
   ```bash
   # Automatically detects Python on your system
   uv venv

   # Or pin a specific Python version (e.g. 3.12)
   uv venv --python 3.12
   ```

3. **Activate the virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt / CMD)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **Linux / macOS**:
     ```bash
     source .venv/bin/activate
     ```

---

### 3. Install Python Dependencies (`pip` or `uv`)

BMALocal relies on the following core Python libraries:

| Library | Min Version | Purpose & Usage in BMALocal |
| :--- | :---: | :--- |
| **`anvil-app-server`** | `>=1.17.0` | Standalone local application server that runs client/server Anvil code |
| **`anvil-uplink`** | `>=0.7.0` | Anvil uplink library for background services and server-to-server RPCs |
| **`websockets`** | `>=17.0` | Asynchronous WebSocket server daemon (integrated in `BMALocal.py`) for live chat |
| **`mysql-connector-python`**| `>=8.0.0` | Official MySQL driver with connection pooling (`pooling.MySQLConnectionPool`) |
| **`python-dotenv`** | `>=1.0.0` | Parses `.env` configuration file for database, paths, and server settings |
| **`pdfkit`** | `>=1.0.0` | Python wrapper for `wkhtmltopdf` to render invoices, quotes & job card PDFs |
| **`openpyxl`** | `>=3.1.0` | Generates and exports Excel spreadsheets for inventory, parts, and revenue |
| **`bcrypt`** | `>=4.0.0` | Cryptographic password hashing and verification for user authentication |
| **`requests`** | `>=2.31.0` | HTTP client for external API calls, analytics, and network testing |

#### Installation Method 1: Using `pip` (Standard)

With your virtual environment activated:
```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Option 1A: Install using requirements.txt (Recommended)
pip install -r requirements.txt

# Option 1B: Install packages manually
pip install anvil-app-server anvil-uplink websockets mysql-connector-python python-dotenv pdfkit openpyxl bcrypt requests
```

#### Installation Method 2: Using `uv` (Lightning Fast)

With your virtual environment activated:
```bash
# Option 2A: Install using requirements.txt with uv
uv pip install -r requirements.txt

# Option 2B: Install packages manually with uv
uv pip install anvil-app-server anvil-uplink websockets mysql-connector-python python-dotenv pdfkit openpyxl bcrypt requests
```

> **Tip for `uv` users:** You can also run commands inside the environment without manual activation using `uv run`:
> ```bash
> uv run python server_code\BMALocal.py
> ```

### 4. Install External Tools (MySQL, Java, wkhtmltopdf)

1. **Java JDK**:
   - Download and install OpenJDK 17 or 21 (e.g., from [Adoptium Eclipse Temurin](https://adoptium.net/)).
   - Verify installation: `java -version`.

2. **wkhtmltopdf**:
   - Download the installer from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html).
   - Standard Windows install path: `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`.

3. **MySQL Server**:
   - Ensure the MySQL service is running.
   - Create the workshop database:
     ```sql
     CREATE DATABASE bmaautoaccessories2017 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
     ```
   - Ensure your database user has full read/write permissions on this database.

### 5. Environment Configuration (.env)

Create a file named `.env` in the root of the project directory (`BMALocal\.env`). Populate it with your local environment values:

```ini
# =============================================================
# BMALocal Configuration File
# =============================================================

# Database Connection (Strictly required)
DB_HOST=localhost
DB_PORT=3306
DB_USER=office
DB_PASSWORD=YourSecurePasswordHere
DB_NAME=bmaautoaccessories2017
DB_AUTH_PLUGIN=mysql_native_password

# Static Asset & Executable Paths (Windows example)
LOGO=D:\BMAAutoAccessories\venv\Lib\site-packages\BMALocal\InvoiceHeaderLogo.jpg
FONT_PATH=D:\BMAAutoAccessories\venv\Lib\site-packages\BMALocal\theme\assets\fonts\MozillaHeadline.ttf
MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe
WKHTMLTOPDF_PATH=C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe

# Real-Time Walkie Talkie WebSocket Server Settings
CHAT_WS_HOST=0.0.0.0
CHAT_WS_PORT=8765

# SSL/TLS Certificates for WSS (Required when running over HTTPS)
CHAT_WS_SSL_CERT=D:\BMAAutoAccessories\venv\Lib\site-packages\BMALocal\cert\192.168.100.12.pem
CHAT_WS_SSL_KEY=D:\BMAAutoAccessories\venv\Lib\site-packages\BMALocal\cert\192.168.100.12-key.pem
```

> **Security Note:** Never commit your `.env` file to version control. It is already included in `.gitignore`.

### 6. SSL/TLS Certificate Setup (for HTTPS & WSS)

When accessing BMALocal from other machines on your local network (e.g., `https://192.168.100.12/`), modern web browsers mandate HTTPS. Because browsers block unencrypted WebSockets (`ws://`) on HTTPS pages due to Mixed Content policies, the WebSocket server must run over secure **WSS** (`wss://`).

You can generate a trusted local development certificate using [mkcert](https://github.com/FiloSottile/mkcert):

```powershell
# Install mkcert local CA
mkcert -install

# Create cert directory
mkdir cert
cd cert

# Generate certificate for your machine's LAN IP address
mkcert 192.168.100.12 localhost 127.0.0.1
```

Rename the generated files to match your `.env` paths (e.g., `192.168.100.12.pem` and `192.168.100.12-key.pem`).

---

## Running the Application

BMALocal consists of two services that run concurrently:
1. **Anvil App Server**: Hosts the web interface, business logic, and UI forms.
2. **Walkie Talkie Chat Server**: Asynchronous WebSocket daemon managing real-time chat, presence, and broadcasts.

### Starting the Anvil App Server

From the project root:

**HTTP Mode (Single-machine local use):**
```powershell
anvil-app-server --app . --port 8080 --auto-migrate
```

**HTTPS Mode (LAN / Multi-machine access):**
```powershell
anvil-app-server --app . --origin https://192.168.100.12:443 --manual-cert-file .\cert\192.168.100.12.pem --manual-cert-key-file .\cert\192.168.100.12-key.pem --auto-migrate
```

### Starting the Walkie Talkie WebSocket Server

The WebSocket server starts automatically in a background daemon thread whenever Anvil App Server runs!
However, if you wish to run the WebSocket server standalone in a separate terminal:
```powershell
python server_code\BMALocal.py
```

On startup, `BMALocal.py` will:
- Read credentials strictly from `.env`.
- Automatically create/verify the `tbl_walkietalkie_messages` and `tbl_walkietalkie_reads` tables in MySQL.
- Bind to the specified `CHAT_WS_HOST` and `CHAT_WS_PORT` (e.g. `0.0.0.0:8765`).
- Enable TLS/WSS if certificates are configured.

---

### Unified Windows Launcher (.bat)

To launch both services and run an automated MySQL backup with a single double-click on Windows, create a batch launcher (e.g., `run_app.bat`):

```cmd
@echo off
SETLOCAL EnableDelayedExpansion

REM ==================================================
REM BMALocal Workshop System Launcher
REM ==================================================
SET "APP_DIR=D:\BMAAutoAccessories\venv\Lib\site-packages\BMALocal"
SET "PYTHON_EXE=D:\BMAAutoAccessories\venv\Scripts\python.exe"
SET "LOG_DIR=%APP_DIR%\logs"
mkdir "%LOG_DIR%" 2>nul

echo ==================================================
echo [1/3] Starting MySQL Automated Backup...
echo ==================================================
REM Load MySQL credentials from .env
for /f "usebackq tokens=1,2 delims==" %%a in ("%APP_DIR%\.env") do (
    set "%%a=%%b"
)

set "BACKUP_DIR=D:\BMAAutoAccessories\Dumps"
mkdir "%BACKUP_DIR%" 2>nul
set "DUMP_FILE=%BACKUP_DIR%\backup_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%.sql"

if exist "%MYSQL_PATH%" (
    "%MYSQL_PATH%" -h %DB_HOST% -P %DB_PORT% -u %DB_USER% --password=%DB_PASSWORD% %DB_NAME% > "%DUMP_FILE%"
    echo [+] Database backup saved to: %DUMP_FILE%
) else (
    echo [!] Warning: mysqldump not found at %MYSQL_PATH%, skipping backup.
)

echo.
echo ==================================================
echo [2/3] Launching Walkie Talkie Chat WebSocket Server...
echo ==================================================
start "BMALocal WebSocket Server" /min "%PYTHON_EXE%" "%APP_DIR%\server_code\BMALocal.py"

echo.
echo ==================================================
echo [3/3] Launching Anvil App Server...
echo ==================================================
cd /d "%APP_DIR%"
anvil-app-server --app . --origin https://192.168.100.12:443 --manual-cert-file "%APP_DIR%\cert\192.168.100.12.pem" --manual-cert-key-file "%APP_DIR%\cert\192.168.100.12-key.pem" --auto-migrate
```

---

## Environment Variables Reference

| Variable | Required? | Default | Description |
| :--- | :---: | :---: | :--- |
| `DB_HOST` | **Yes** | `localhost` | Hostname or IP of the MySQL database server |
| `DB_PORT` | **Yes** | `3306` | MySQL TCP port |
| `DB_USER` | **Yes** | — | MySQL username |
| `DB_PASSWORD` | **Yes** | — | MySQL password |
| `DB_NAME` | **Yes** | — | MySQL database name (e.g. `bmaautoaccessories2017`) |
| `DB_AUTH_PLUGIN`| No | `mysql_native_password`| Authentication plugin for MySQL connector |
| `CHAT_WS_HOST` | **Yes** | `0.0.0.0` | IP interface on which the WebSocket server listens |
| `CHAT_WS_PORT` | **Yes** | `8765` | TCP port on which the WebSocket server listens |
| `CHAT_WS_SSL_CERT`| No | — | Absolute path to SSL `.pem` certificate for WSS |
| `CHAT_WS_SSL_KEY` | No | — | Absolute path to SSL private key `.pem` for WSS |
| `WKHTMLTOPDF_PATH`| **Yes** | — | Absolute path to `wkhtmltopdf.exe` |
| `MYSQL_PATH` | No | — | Absolute path to `mysqldump.exe` for automated backups |
| `LOGO` | No | — | Absolute path to company logo used in invoice headers |
| `FONT_PATH` | No | — | Path to custom typography fonts |

---

## Project Directory Structure

```text
BMALocal/
├── anvil.yaml                      # Anvil application manifest, schemas, tables & dependencies
├── requirements.txt                # Python package dependencies for pip and uv
├── .env                            # Local environment & secret variables (gitignored)
├── README.md                       # Comprehensive project documentation
├── cert/                           # Local SSL certificates for HTTPS and WSS
│   ├── 192.168.100.12.pem
│   └── 192.168.100.12-key.pem
├── client_code/                    # Front-end Anvil UI Forms & Logic (Python)
│   ├── Main/                       # Root application shell & sidebar navigation
│   ├── JobCard/                    # Job card creation, checklist & inspection
│   ├── Contacts/                   # Customer, supplier, staff directory
│   ├── Booking/                    # Appointment & bay schedule management
│   ├── Workflow/                   # Live technician repair pipeline
│   ├── ProgressTracker/            # Visual repair milestone tracker (desktop)
│   ├── ProgressTrackerMobileView/  # Visual repair milestone tracker (mobile)
│   ├── Inventory/                  # Parts stock, bins, locations & stocktaking
│   ├── PartsHub/                   # Catalog, supplier mapping, buying/selling pricing
│   ├── Payment/                    # Invoices, receipts, partial payments
│   ├── Quote/                      # Quotation & interim estimate builder
│   ├── SelfService/                # Kiosk & customer self-service portal
│   ├── SignatureComponent.py       # Digital canvas signature capture component
│   ├── WalkieTalkieChat.py         # Anvil wrapper for live WebSocket chat
│   └── ModNavigation/              # Global form routing controller
├── server_code/                    # Backend server-side services (Python)
│   └── BMALocal.py                 # Core server functions, DB queries & integrated WebSocket server
└── theme/                          # Visual theme, assets, HTML templates & styles
    ├── parameters.yaml             # Theme roles and color tokens
    └── assets/
        ├── standard-page.html      # Master HTML page shell
        ├── theme.css               # Comprehensive application CSS
        ├── walkietalkie.html       # Chat popup layout template
        ├── walkietalkie.js         # Chat WebSocket client & DOM controller
        ├── signature.js            # Canvas signature handling logic
        └── barcode.js              # Barcode scanner reader integration
```

---

## Maintenance & Troubleshooting

### 1. Mixed Content Error in Browser (`ws://` vs `wss://`)
- **Problem**: When loading the page over `https://...`, the browser console reports: `Mixed Content: The page was loaded over HTTPS, but attempted to connect to insecure WebSocket endpoint 'ws://...'`.
- **Solution**: Ensure `CHAT_WS_SSL_CERT` and `CHAT_WS_SSL_KEY` are configured in `.env` and point to valid `.pem` certificate files. `walkietalkie.js` will automatically switch from `ws://` to `wss://`.

### 2. WebSocket Server Connection Refused (`ws://...:8765`)
- **Problem**: Chat status shows "Offline (Reconnecting...)".
- **Solution**:
  1. Check if the WebSocket server is running: `Get-NetTCPConnection -LocalPort 8765`.
  2. Verify firewall rules allow incoming TCP traffic on port `8765`.
  3. Start the server manually: `python server_code\BMALocal.py`.

### 3. PDF Generation Fails
- **Problem**: Error when attempting to generate invoices or job card PDFs.
- **Solution**: Verify `WKHTMLTOPDF_PATH` in `.env` points directly to the installed `wkhtmltopdf.exe` binary. Test it in the terminal with: `wkhtmltopdf --version`.

### 4. Database Connection Errors
- **Problem**: `mysql.connector.errors.ProgrammingError: Access denied for user`.
- **Solution**: Check credentials in `.env`. If using MySQL 8.0+, ensure the user is configured with `IDENTIFIED WITH mysql_native_password BY 'your_password'` or update `DB_AUTH_PLUGIN` to match your MySQL configuration.

---

## License & Support

BMALocal is proprietary software developed for **BMA Auto Accessories**. All rights reserved. For internal setup assistance, contact your system administrator or workshop engineering team.
