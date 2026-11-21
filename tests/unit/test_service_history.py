import base64
import datetime
import importlib
import json
from pathlib import Path
import subprocess
import sys
import types
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest


class FakeMedia:
    def __init__(self, content_type, data, name=None):
        self.content_type = content_type
        self.data = data
        self.name = name

    def get_bytes(self):
        return self.data


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _load_selfservice_module(monkeypatch):
    server = _module(
        "anvil.server",
        call=MagicMock(return_value=True),
        call_s=MagicMock(return_value=42),
    )
    anvil = _module("anvil", BlobMedia=FakeMedia, server=server, users=MagicMock())
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    stubs = {
        "anvil": anvil,
        "anvil.server": server,
        "anvil.users": anvil.users,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.js": _module("anvil.js", call=MagicMock()),
        "client_code.SelfService._anvil_designer": _module(
            "client_code.SelfService._anvil_designer",
            SelfServiceTemplate=type("SelfServiceTemplate", (), {}),
        ),
    }
    target_module = "client_code.SelfService"
    monkeypatch.delitem(sys.modules, target_module, raising=False)
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    return importlib.import_module(target_module), anvil


class SequenceCursor:
    """Fake DB cursor that records executed parameterized queries and returns queued result sets."""

    def __init__(self, result_sets):
        self._result_sets = list(result_sets)
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        if not self._result_sets:
            return []
        return self._result_sets.pop(0)

    def fetchone(self):
        rows = self.fetchall()
        return rows[0] if rows else None


@pytest.fixture
def technician_portal():
    from server_code import BMALocal  # noqa: F401 - ensures cross-module wiring
    from server_code import technician_portal as tp

    return tp


# =============================================================================
# Backend: get_vehicle_service_history
# =============================================================================


def test_get_vehicle_service_history_happy_path(monkeypatch, technician_portal):
    f1_fields = json.dumps([
        {"name": "chk_final", "label": "Final Quality", "value": True},
        {"name": "txt_next_service_mileage", "label": "Enter Next Service Mileage", "value": "95000"},
    ])
    fake_cursor = SequenceCursor([
        # 1. tbl_jobcarddetails
        [
            (
                101,
                datetime.date(2026, 11, 15),
                "JC-2026-101",
                "KDA 234S",
                "Toyota Prado",
                85000,
                "<p>Major service</p><p>Check brakes</p>",
                "Front bumper scratch",
                "Completed",
                1,
            ),
            (
                88,
                datetime.date(2025, 6, 10),
                "JC-2025-088",
                "KDA234S",
                "Toyota Prado",
                75000,
                "Oil change",
                "",
                None,
                1,
            ),
        ],
        # 2. tbl_pendingassignedjobs + tbl_technicians
        [(101, "ALEX MEDINA"), (88, "JANE DOE")],
        # 3. tbl_workdoneinjobcard
        [(101, "Replaced oil filter and front brake pads.")],
        # 4. tbl_techniciandefectsandrequestedparts
        [(101, "Worn front brake pads\nMinor oil seepage")],
        # 5. tbl_invoices (Item, Part_No, QuantityIssued — no Amount!)
        [
            (101, "Engine Oil 5W-30", "OIL-5W30", 5.0),
            (101, "Oil Filter", "OF-123", 1.0),
            (101, "Brake Fluid", "", 0.5),
        ],
        # 6. tbl_technicianinspectionchecklist
        [(101, "F1", f1_fields)],
        # 7. tbl_vehicleinspectionimages
        [(101,)],
    ])

    @contextmanager
    def fake_db_cursor():
        yield fake_cursor

    monkeypatch.setattr(technician_portal, "_get_current_user", lambda: {"id": 1, "role": "Technician"})
    monkeypatch.setattr(technician_portal, "db_cursor", fake_db_cursor)

    result = technician_portal.get_vehicle_service_history("  kda 234-s  ")

    assert result["reg_no"] == "KDA234S"
    assert result["make_and_model"] == "Toyota Prado"
    assert len(result["records"]) == 2

    first = result["records"][0]
    assert first["jobcard_id"] == 101
    assert first["date"] == "2026-11-15"
    assert first["jobcard_ref"] == "JC-2026-101"
    assert first["status"] == "Completed"
    assert first["technician"] == "ALEX MEDINA"
    assert first["mileage"] == 85000
    assert first["next_service_mileage"] == "95000"
    assert first["client_instruction"] == "Major service\nCheck brakes"
    assert first["notes"] == "Front bumper scratch"
    assert first["defects"] == "Worn front brake pads\nMinor oil seepage"
    assert first["work_done"] == "Replaced oil filter and front brake pads."
    assert first["parts_and_services"] == [
        {"item": "Engine Oil 5W-30", "part_no": "OIL-5W30", "quantity": "5"},
        {"item": "Oil Filter", "part_no": "OF-123", "quantity": "1"},
        {"item": "Brake Fluid", "part_no": "", "quantity": "0.5"},
    ]
    assert first["has_inspection"] is True

    # Ensure prices/amounts are never selected or exposed
    for part in first["parts_and_services"]:
        assert "amount" not in part
        assert "price" not in part

    # Verify second (legacy NULL status with IsComplete=1) record
    second = result["records"][1]
    assert second["status"] == "Completed"
    assert second["has_inspection"] is False
    assert second["parts_and_services"] == []

    # Verify exact normalized SQL parameter and cancelled exclusion
    job_query, job_params = fake_cursor.executed[0]
    assert job_params == ("KDA234S",)
    assert "Cancel Jobcard" in job_query
    assert "Amount" not in fake_cursor.executed[4][0]


def test_get_vehicle_service_history_no_matches(monkeypatch, technician_portal):
    fake_cursor = SequenceCursor([[]])

    @contextmanager
    def fake_db_cursor():
        yield fake_cursor

    monkeypatch.setattr(technician_portal, "_get_current_user", lambda: {"id": 1})
    monkeypatch.setattr(technician_portal, "db_cursor", fake_db_cursor)

    result = technician_portal.get_vehicle_service_history("KZZ 999Z")

    assert result == {"reg_no": "KZZ999Z", "make_and_model": "", "records": []}
    assert len(fake_cursor.executed) == 1


@pytest.mark.parametrize("bad_reg", [None, "", "   ", "---", 12345, "A" * 51])
def test_get_vehicle_service_history_rejects_invalid_input(monkeypatch, technician_portal, bad_reg):
    monkeypatch.setattr(technician_portal, "_get_current_user", lambda: {"id": 1})

    with pytest.raises(ValueError, match="valid vehicle registration"):
        technician_portal.get_vehicle_service_history(bad_reg)


def test_get_vehicle_service_history_rejects_unauthenticated(monkeypatch, technician_portal):
    def deny():
        raise PermissionError("Authentication required")

    monkeypatch.setattr(technician_portal, "_get_current_user", deny)

    with pytest.raises(PermissionError, match="Authentication required"):
        technician_portal.get_vehicle_service_history("KDA234S")


# =============================================================================
# Backend: get_service_history_inspection
# =============================================================================


def test_get_service_history_inspection_happy_path(monkeypatch, technician_portal):
    fake_cursor = SequenceCursor([
        [
            (
                "B2",
                "B",
                "B. CUSTOMER COMPLAINT & DIAGNOSIS",
                "Diagnostic scan",
                1,
                json.dumps([{"name": "text_box_fault_code", "label": "Fault Codes", "value": "P0420"}]),
            ),
        ]
    ])

    @contextmanager
    def fake_db_cursor():
        yield fake_cursor

    photo_1 = FakeMedia("image/png", b"\x89PNG\r\n\x1a\nphoto1")
    monkeypatch.setattr(technician_portal, "_get_current_user", lambda: {"id": 1})
    monkeypatch.setattr(technician_portal, "db_cursor", fake_db_cursor)
    monkeypatch.setattr(
        technician_portal,
        "get_vehicle_inspection_data",
        lambda jid: {"images": {"image_1": photo_1, "image_2": None, "image_3": None}},
    )

    result = technician_portal.get_service_history_inspection(101)

    assert len(result["checklist"]) == 1
    assert result["checklist"][0]["item_code"] == "B2"
    assert result["checklist"][0]["is_checked"] is True
    assert result["checklist"][0]["fields"] == [
        {"name": "text_box_fault_code", "label": "Fault Codes", "value": "P0420"}
    ]
    assert result["images"]["image_1"] is photo_1
    assert result["images"]["image_2"] is None
    assert result["images"]["image_3"] is None


@pytest.mark.parametrize("bad_id", [0, -5, "101", None, True])
def test_get_service_history_inspection_rejects_invalid_id(monkeypatch, technician_portal, bad_id):
    monkeypatch.setattr(technician_portal, "_get_current_user", lambda: {"id": 1})

    with pytest.raises(ValueError, match="Invalid job card ID"):
        technician_portal.get_service_history_inspection(bad_id)


def test_get_service_history_inspection_rejects_unauthenticated(monkeypatch, technician_portal):
    def deny():
        raise PermissionError("Authentication required")

    monkeypatch.setattr(technician_portal, "_get_current_user", deny)

    with pytest.raises(PermissionError, match="Authentication required"):
        technician_portal.get_service_history_inspection(101)


# =============================================================================
# Client Bridge: SelfService form methods
# =============================================================================


def test_selfservice_bridge_get_service_history_and_inspection(monkeypatch):
    module, anvil = _load_selfservice_module(monkeypatch)
    form = object.__new__(module.SelfService)

    history_payload = {"reg_no": "KDA234S", "make_and_model": "BMW X5", "records": []}
    anvil.server.call.return_value = history_payload
    assert form.getServiceHistory("KDA 234S") == history_payload
    anvil.server.call.assert_called_with("get_vehicle_service_history", "KDA 234S")

    anvil.server.call.return_value = {
        "checklist": [{"item_code": "A1", "is_checked": True, "fields": []}],
        "images": {
            "image_1": FakeMedia("image/png", b"\x89PNG\r\n\x1a\nabc"),
            "image_2": None,
            "image_3": None,
        },
    }
    inspection = form.getServiceHistoryInspection("101")
    anvil.server.call.assert_called_with("get_service_history_inspection", 101)
    assert inspection["checklist"] == [{"item_code": "A1", "is_checked": True, "fields": []}]
    expected_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\nabc").decode("ascii")
    assert inspection["images"]["image_1"] == f"data:image/png;base64,{expected_b64}"
    assert inspection["images"]["image_2"] is None
    assert inspection["images"]["image_3"] is None


# =============================================================================
# Frontend: selfservice.js structure, syntax & helpers
# =============================================================================


def test_selfservice_js_syntax_and_service_history_button_placement():
    js_path = Path(__file__).parents[2] / "theme" / "assets" / "selfservice.js"
    source = js_path.read_text(encoding="utf-8")

    # 1. Valid JS syntax
    syntax_check = subprocess.run(
        ["node", "--check", str(js_path)],
        capture_output=True,
        check=False,
        text=True,
    )
    assert syntax_check.returncode == 0, syntax_check.stderr

    # 2. Service History button immediately follows In-Service button
    in_service_idx = source.index("filterByStatus('In-Service')")
    service_history_idx = source.index('id="service-history-btn"')
    assert in_service_idx < service_history_idx
    assert service_history_idx - in_service_idx < 250

    # 3. Auto-refresh does not wipe open Service History panel
    assert "if (!state.serviceHistoryOpen)" in source


def test_selfservice_js_service_history_helpers():
    js_path = Path(__file__).parents[2] / "theme" / "assets" / "selfservice.js"
    source = js_path.read_text(encoding="utf-8")

    start = source.index("    function normalizeServiceHistoryReg(")
    end = source.index("    function renderServiceHistoryPanel()", start)
    helpers = source[start:end]

    script = f"""
        function sanitizeHTML(str) {{
            return String(str || '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        }}
        {helpers}
        if (normalizeServiceHistoryReg('  kda 234-s ') !== 'KDA234S') {{
            throw new Error('normalizeServiceHistoryReg failed');
        }}
        if (getServiceHistoryStatusClass('In Service') !== 'status-in-service') {{
            throw new Error('getServiceHistoryStatusClass failed');
        }}
        const partsHtml = formatHistoryParts([
            {{ item: 'Oil <Filter>', part_no: 'OF-1', quantity: '2' }}
        ]);
        if (!partsHtml.includes('Oil &lt;Filter&gt;') || !partsHtml.includes('[OF-1]') || !partsHtml.includes('2')) {{
            throw new Error('formatHistoryParts output unexpected: ' + partsHtml);
        }}
        if (!formatHistoryParts([]).includes('—')) {{
            throw new Error('Empty parts should render dash');
        }}
        const state = {{
            serviceHistoryOpen: true,
            serviceHistoryQuery: 'KDA 234S',
            serviceHistoryLastSearched: 'KDA234S',
            serviceHistoryMakeModel: 'Toyota Prado',
            serviceHistoryResults: [{{ jobcard_id: 1 }}],
            serviceHistoryLoading: true,
            serviceHistoryError: 'boom',
            serviceHistoryHasSearched: true
        }};
        let modalClosed = false;
        function closeServiceHistoryInspection() {{ modalClosed = true; }}
        resetServiceHistoryState();
        if (!modalClosed || state.serviceHistoryOpen || state.serviceHistoryQuery !== '' ||
                state.serviceHistoryLastSearched !== '' || state.serviceHistoryMakeModel !== '' ||
                state.serviceHistoryResults.length !== 0 || state.serviceHistoryLoading ||
                state.serviceHistoryError !== '' || state.serviceHistoryHasSearched) {{
            throw new Error('resetServiceHistoryState did not clear all service history state');
        }}
    """
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
