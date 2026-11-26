import importlib
import sys
import types
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import server_code.BMALocal as bma
from server_code import _common, job_cards, people, quotations


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def test_get_jobcard_form_data_happy_invalid_and_unauth():
    cursor = MagicMock()
    cursor.fetchone.return_value = (
        42, 10, "KDA 123A", "BMW X5", "WBA1234567890",
        "3000", "ENG1", "N55", 0, 1,
        "A52", 1, 0, "JC-0042", "2026-11-01", "2026-11-05", "2026-11-06",
        3, 1, 1, 1, "Jack + spare", "85000",
        0, 0, 1, 0, 0,
        "Check brakes", "Front pads worn", "In Service",
        "Jane Staff", "John Tech", "<div>Replaced pads</div><br><div>Bled brakes</div>",
    )

    with patch.object(job_cards, "_get_current_user"), \
         patch.object(job_cards, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        res = bma.get_jobcard_form_data(42)

    assert db_ctx.call_count == 1
    assert res["ID"] == 42
    assert res["JobCardRef"] == "JC-0042"
    assert res["CheckedInByName"] == "Jane Staff"
    assert res["AssignedTechnician"] == "John Tech"
    assert res["WorkDone"] == "Replaced padsBled brakes"

    cursor.fetchone.return_value = None
    with patch.object(job_cards, "_get_current_user"), \
         patch.object(job_cards, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        assert bma.get_jobcard_form_data(999) is None

    with patch.object(job_cards, "_get_current_user"):
        for bad_id in (None, 0, -5, True, "abc"):
            with pytest.raises(ValueError, match="Invalid job_id"):
                bma.get_jobcard_form_data(bad_id)

    with patch.object(job_cards, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.get_jobcard_form_data(42)


def test_get_defects_form_init_data_uses_limit_1_and_caches_staff():
    _common.invalidate_lookup_cache()
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [("Check oil", "Leak", "Oil pan", "1000", "Filter", "Oil filter", "Jane", b"png-bytes")],
        [("Jane",), ("John Tech",)],
        [("Check oil", "Leak", "Oil pan", "1000", "Filter", "Oil filter", "Jane", b"png-bytes")],
    ]

    with patch.object(job_cards, "_get_current_user"), \
         patch.object(job_cards, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        first = bma.get_defects_form_init_data(42)
        second = bma.get_defects_form_init_data(42)

    assert len(first["defects_list"]) == 1
    assert first["staff_names"] == [("Jane", "Jane"), ("John Tech", "John Tech")]
    assert second["staff_names"] == first["staff_names"]
    # First call: 1 defects query + 1 staff query. Second call: 1 defects query only (staff served from cache).
    assert cursor.execute.call_count == 3
    first_sql = cursor.execute.call_args_list[0].args[0]
    assert "LIMIT 1" in first_sql

    # Invalid input & unauthorized checks
    with patch.object(job_cards, "_get_current_user"):
        with pytest.raises(ValueError, match="Invalid job_id"):
            bma.get_defects_form_init_data(0)
    with patch.object(job_cards, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.get_defects_form_init_data(42)

    _common.invalidate_lookup_cache()


def test_get_quote_details_by_job_id_includes_jobcard_ref():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        ("Alice", "BMW X3", "KDB 456B", "2026-11-01", "CH123", "B48", "50000", "Oil Filter", 2, 1500.0, 42, "JC-0042-IQ"),
    ]

    with patch.object(quotations, "_get_current_user"), \
         patch.object(quotations, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        rows = bma.get_quote_details_by_job_id(42)

    assert len(rows) == 1
    assert rows[0]["JobCardRef"] == "JC-0042-IQ"
    assert rows[0]["Total"] == 3000.0


def test_get_progress_tracker_modals_bundle_happy_invalid_and_unauth():
    cursor = MagicMock()
    fake_jc = {"ID": 42, "JobCardRef": "JC-0042"}
    fake_defects = {"defects_list": [], "fallback": None, "staff_names": []}

    with patch.object(job_cards, "_get_current_user"), \
         patch.object(job_cards, "db_cursor") as db_ctx, \
         patch.object(job_cards, "_fetch_jobcard_form_data", return_value=fake_jc), \
         patch.object(job_cards, "_fetch_defects_form_init_data", return_value=fake_defects), \
         patch.object(job_cards, "get_quote_details_by_job_id", return_value=[{"Item": "Oil"}]), \
         patch.object(job_cards, "get_quote_confirmation_details_by_job_id", return_value=[]), \
         patch.object(job_cards, "get_invoice_details_by_job_id", return_value=[]), \
         patch.object(job_cards, "getPaymentsDetails", return_value=[]):
        db_ctx.return_value.__enter__.return_value = cursor
        bundle = bma.get_progress_tracker_modals_bundle(42)

    assert bundle["jobcard"] == fake_jc
    assert bundle["defects"] == fake_defects
    assert bundle["quote"] == [{"Item": "Oil"}]
    assert bundle["confirm"] == []
    assert bundle["invoice"] == []
    assert bundle["payment"] == []

    with patch.object(job_cards, "_get_current_user"):
        with pytest.raises(ValueError, match="Invalid job_id"):
            bma.get_progress_tracker_modals_bundle(None)

    with patch.object(job_cards, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.get_progress_tracker_modals_bundle(42)


def _load_tracker_module(monkeypatch, module_name, template_name):
    alert_mock = MagicMock()
    notif_instance = MagicMock()
    server_call = MagicMock()
    server_call_s = MagicMock()
    timer = MagicMock()

    anvil = _module("anvil", Notification=MagicMock(return_value=notif_instance), alert=alert_mock)
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module(
        "anvil.server",
        call=server_call,
        call_s=server_call_s,
        no_loading_indicator=nullcontext(),
    )
    anvil_users = _module("anvil.users")
    anvil_js = _module("anvil.js", window=SimpleNamespace(setTimeout=timer))
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.users = anvil_users
    anvil.js = anvil_js

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "anvil.js": anvil_js,
        f"client_code.{module_name}._anvil_designer": _module(
            f"client_code.{module_name}._anvil_designer",
            **{template_name: type(template_name, (), {})},
        ),
    }

    for sub_mod, cls_name in (
        ("JobCardForm", "JobCardForm"),
        ("DefectsForm", "DefectsForm"),
        ("QuoteForm", "QuoteForm"),
        ("ConfirmForm", "ConfirmForm"),
        ("InvoiceForm", "InvoiceForm"),
        ("PaymentForm", "PaymentForm"),
        ("VehicleInspectionChecklist", "VehicleInspectionChecklist"),
    ):
        stubs[f"client_code.{sub_mod}"] = _module(
            f"client_code.{sub_mod}",
            **{cls_name: MagicMock(name=cls_name)},
        )

    target = f"client_code.{module_name}"
    monkeypatch.delitem(sys.modules, target, raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)

    mod = importlib.import_module(target)
    return mod, server_call, server_call_s, alert_mock


def test_progress_tracker_uses_prefetched_cache_with_zero_server_calls_on_click(monkeypatch):
    mod, server_call, server_call_s, alert_mock = _load_tracker_module(
        monkeypatch, "ProgressTracker", "ProgressTrackerTemplate"
    )
    try:
        cls = mod.ProgressTracker
        form = SimpleNamespace(
            drop_down_JobCardRefDetails=SimpleNamespace(selected_value=42),
            btn_JobCard=SimpleNamespace(enabled=True),
            btn_Defects=SimpleNamespace(enabled=True),
            btn_Quotation=SimpleNamespace(enabled=True),
            btn_Confirmed=SimpleNamespace(enabled=True),
            btn_Invoice=SimpleNamespace(enabled=True),
            btn_Payment=SimpleNamespace(enabled=True),
            _modals_cache={},
            _modals_cache_job_id=None,
        )
        form._invalidate_modals_cache = lambda jid=None: cls._invalidate_modals_cache(form, jid)
        form._prefetch_modals = lambda jid: cls._prefetch_modals(form, jid)
        form._schedule_prefetch_modals = MagicMock()
        form._get_cached_or_fetch = lambda jid, key, fn: cls._get_cached_or_fetch(form, jid, key, fn)

        server_call_s.return_value = {
            "jobcard": {"ID": 42, "JobCardRef": "JC-0042"},
            "defects": {"defects_list": [], "fallback": None, "staff_names": []},
            "quote": [{"Item": "Oil", "JobCardRef": "JC-0042"}],
            "confirm": [{"Item": "Oil"}],
            "invoice": [{"Item": "Oil"}],
            "payment": [{"PaymentID": 1}],
        }

        cls._prefetch_modals(form, 42)
        assert form._modals_cache_job_id == 42

        # Clicking Quote / Confirm / Invoice makes ZERO blocking server calls
        cls.btn_Quotation_click(form)
        cls.btn_Confirmed_click(form)
        cls.btn_Invoice_click(form)
        assert server_call.call_count == 0
        assert alert_mock.call_count == 3
        assert form.btn_Quotation.enabled is True
        assert form.btn_Confirmed.enabled is True
        assert form.btn_Invoice.enabled is True
    finally:
        sys.modules.pop("client_code.ProgressTracker", None)


def test_progress_tracker_mobile_reenables_buttons_when_data_missing(monkeypatch):
    mod, server_call, server_call_s, alert_mock = _load_tracker_module(
        monkeypatch, "ProgressTrackerMobileView", "ProgressTrackerMobileViewTemplate"
    )
    try:
        cls = mod.ProgressTrackerMobileView
        form = SimpleNamespace(
            drop_down_JobCardRefDetails=SimpleNamespace(selected_value=42),
            btn_Quotation=SimpleNamespace(enabled=True),
            btn_Invoice=SimpleNamespace(enabled=True),
            btn_Payment=SimpleNamespace(enabled=True),
            _modals_cache={"quote": [], "invoice": [], "payment": []},
            _modals_cache_job_id=42,
        )
        form._get_cached_or_fetch = lambda jid, key, fn: cls._get_cached_or_fetch(form, jid, key, fn)

        cls.btn_Quotation_click(form)
        cls.btn_Invoice_click(form)
        cls.btn_Payment_click(form)

        assert form.btn_Quotation.enabled is True
        assert form.btn_Invoice.enabled is True
        assert form.btn_Payment.enabled is True
        assert server_call.call_count == 0
    finally:
        sys.modules.pop("client_code.ProgressTrackerMobileView", None)
