import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_bmalocal_import_does_not_eagerly_load_heavy_libraries():
    """Importing server_code.BMALocal must not eagerly import openpyxl, pdfkit, bcrypt, or websockets."""
    script = (
        "import sys, json; "
        "import server_code.BMALocal; "
        "heavy = ['openpyxl', 'pdfkit', 'bcrypt', 'websockets']; "
        "loaded = [m for m in heavy if m in sys.modules]; "
        "print(json.dumps(loaded))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    loaded = json.loads(proc.stdout.strip().splitlines()[-1])
    assert loaded == [], f"Heavy libraries were eagerly imported on startup: {loaded}"


def test_common_lazy_getters_and_getattr_compatibility():
    """Verify lazy helpers and PEP 562 __getattr__ resolve optional heavy libraries on demand."""
    from server_code import _common

    assert callable(_common.get_pdfkit)
    assert callable(_common.get_pdfkit_config)
    assert callable(_common.get_bcrypt)
    assert callable(_common.get_websockets)

    bcrypt_mod = _common.get_bcrypt()
    assert hasattr(bcrypt_mod, "hashpw")
    assert _common.bcrypt is bcrypt_mod

    ws_mod = _common.get_websockets()
    assert hasattr(ws_mod, "serve")
    assert _common.websockets is ws_mod


def test_main_sidebar_permission_buttons_default_hidden_in_yaml():
    """Permission-gated sidebar buttons must default to visible: false to prevent unauthorized button flash."""
    template_path = REPO_ROOT / "client_code" / "Main" / "form_template.yaml"
    content = template_path.read_text(encoding="utf-8")

    gated_buttons = [
        "btn_Contact",
        "btn_JobCard",
        "btn_Booking",
        "btn_Workflow",
        "btn_Tracker",
        "btn_Revision",
        "btn_Payment",
        "btn_Inventory",
        "btn_Report",
        "btn_PartsHub",
        "btn_Settings",
        "btn_ResetPassword",
        "btn_FAQs",
    ]

    for btn in gated_buttons:
        pattern = rf"name:\s*{re.escape(btn)}\r?\n\s*properties:\s*\{{([^}}]+)\}}"
        match = re.search(pattern, content)
        assert match, f"Missing sidebar button {btn} in Main/form_template.yaml"
        assert "visible: false" in match.group(1), f"{btn} must have visible: false by default"

    logout_match = re.search(r"name:\s*btn_Logout\r?\n\s*properties:\s*\{([^}]+)\}", content)
    assert logout_match, "Missing btn_Logout in Main/form_template.yaml"
    assert "visible: false" not in logout_match.group(1)


def test_section_containers_defer_subform_imports_and_use_show_event():
    """Contacts, Settings, PartsHub, Revision, and Report must not eagerly import heavy subforms at top level."""
    checks = {
        "Contacts": ["from ..Client import Client", "from ..Tehnicians import Tehnicians", "from ..Staffs import Staffs"],
        "Settings": ["from ..UserAccounts import UserAccounts", "from ..UserRolesAndPermissions import UserRolesAndPermissions"],
        "PartsHub": ["from ..PartsCatalog import PartsCatalog", "from ..OrderTracking import OrderTracking"],
        "Report": [
            "from ..ClientContactReport import ClientContactReport",
            "from ..InventoryReport import InventoryReport",
            "from ..PeriodicPayment import PeriodicPayment",
        ],
    }
    for form_name, forbidden_top_imports in checks.items():
        source = (REPO_ROOT / "client_code" / form_name / "__init__.py").read_text(encoding="utf-8")
        top_lines = "\n".join(source.splitlines()[:20])
        for imp in forbidden_top_imports:
            assert imp not in top_lines, f"{form_name} still eagerly imports {imp!r} at module top level"
