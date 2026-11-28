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
        7, "Alice Client", "0712345678", "Nairobi", "alice@example.com",
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
    assert res["AssignedTechnicianID"] == 7
    assert res["ClientFullname"] == "Alice Client"
    assert res["ClientPhone"] == "0712345678"
    assert res["ClientAddress"] == "Nairobi"
    assert res["ClientEmail"] == "alice@example.com"
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
    from server_code import invoices

    cursor = MagicMock()
    fake_jc = {"ID": 42, "JobCardRef": "JC-0042", "ClientInstruction": "Check", "Notes": "None"}
    fake_defects = {"defects_list": [], "fallback": None, "staff_names": []}

    with patch.object(job_cards, "_get_current_user") as auth_mock, \
         patch.object(job_cards, "db_cursor") as db_ctx, \
         patch.object(job_cards, "_fetch_jobcard_form_data", return_value=fake_jc), \
         patch.object(job_cards, "_fetch_defects_form_init_data", return_value=fake_defects), \
         patch.object(quotations, "_fetch_quote_details_by_job_id", return_value=[{"Item": "Oil"}]), \
         patch.object(quotations, "_fetch_quote_confirmation_details_by_job_id", return_value=[]), \
         patch.object(invoices, "_fetch_invoice_details_by_job_id", return_value=[]), \
         patch.object(invoices, "_fetch_payments_details", return_value=[]):
        db_ctx.return_value.__enter__.return_value = cursor
        bundle = bma.get_progress_tracker_modals_bundle(42)

    # Single auth check and single DB connection checkout across all 6 modals
    assert auth_mock.call_count == 1
    assert db_ctx.call_count == 1
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
        alert_mock.return_value = False
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
            _prewarmed_modals={},
        )
        form._evict_lru_job = lambda jid=None: cls._evict_lru_job(form, jid)
        form._invalidate_modals_cache = lambda jid=None: cls._invalidate_modals_cache(form, jid)
        form._build_modal_instance = lambda jid, k, d: cls._build_modal_instance(form, jid, k, d)
        form._prewarm_for_bundle = lambda jid, b, p, k: cls._prewarm_for_bundle(form, jid, b, p, k)
        form._prewarm_single_modal = lambda jid, k: cls._prewarm_single_modal(form, jid, k)
        form._schedule_prewarm_single_modal = MagicMock()
        form._schedule_prewarm_modals = MagicMock()
        form._pop_or_build_modal = lambda jid, k, d: cls._pop_or_build_modal(form, jid, k, d)
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
        form._schedule_prewarm_modals.assert_called_once_with(42)

        # Simulate idle pre-warming completing for all 6 modals
        for key in ("jobcard", "defects", "quote", "confirm", "invoice", "payment"):
            cls._prewarm_single_modal(form, 42, key)
        assert len(form._prewarmed_modals) == 6
        mod.JobCardForm.reset_mock()
        mod.DefectsForm.reset_mock()
        mod.QuoteForm.reset_mock()
        mod.ConfirmForm.reset_mock()
        mod.InvoiceForm.reset_mock()
        mod.PaymentForm.reset_mock()

        # Clicking ALL 6 buttons makes ZERO server calls AND ZERO synchronous form constructions!
        cls.btn_JobCard_click(form)
        cls.btn_Defects_click(form)
        cls.btn_Quotation_click(form)
        cls.btn_Confirmed_click(form)
        cls.btn_Invoice_click(form)
        cls.btn_Payment_click(form)
        assert server_call.call_count == 0
        assert alert_mock.call_count == 6
        assert mod.JobCardForm.call_count == 0
        assert mod.DefectsForm.call_count == 0
        assert mod.QuoteForm.call_count == 0
        assert mod.ConfirmForm.call_count == 0
        assert mod.InvoiceForm.call_count == 0
        assert mod.PaymentForm.call_count == 0
        # Read-only close keeps _modals_cache warm and schedules single-modal re-prewarm
        assert form._modals_cache_job_id == 42
        assert form._schedule_prewarm_single_modal.call_count == 6
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


def _load_edit_jobcard_module(monkeypatch):
    server_call = MagicMock()
    server_call_s = MagicMock()
    mod_get_data = _module(
        "client_code.ModGetData",
        getTechniciansCached=MagicMock(return_value=[{"ID": 7, "Fullname": "John Tech"}]),
        getStaffCached=MagicMock(return_value=[{"ID": 3, "Staff": "Jane Staff"}]),
    )
    anvil = _module("anvil", Notification=MagicMock(), alert=MagicMock(), get_open_form=MagicMock())
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=server_call, call_s=server_call_s)
    anvil_users = _module("anvil.users")
    anvil_js = _module("anvil.js", call=MagicMock())
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
        "client_code.ModGetData": mod_get_data,
        "client_code.EditJobCard._anvil_designer": _module(
            "client_code.EditJobCard._anvil_designer",
            EditJobCardTemplate=type("EditJobCardTemplate", (), {}),
        ),
    }

    target = "client_code.EditJobCard"
    monkeypatch.delitem(sys.modules, target, raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)

    mod = importlib.import_module(target)
    return mod, server_call, server_call_s, mod_get_data


def _make_edit_jobcard_form(cls):
    def _box():
        return SimpleNamespace(text="")

    def _date():
        return SimpleNamespace(date=None)

    def _chk():
        return SimpleNamespace(checked=False)

    form = SimpleNamespace(
        label_ID=_box(),
        search_keyword_1=SimpleNamespace(set_result=MagicMock(), text_box_search=_box()),
        search_keyword_4=SimpleNamespace(set_result=MagicMock(), text_box_search=_box()),
        txt_ClientName=_box(),
        drop_down_selectCustomer=SimpleNamespace(
            include_placeholder=True, items=[], selected_value=None
        ),
        txt_PhoneNo=_box(),
        txt_Address=_box(),
        txt_Email=_box(),
        txt_JobCardRef=_box(),
        txtDueDate=_date(),
        txtReceivedDate=_date(),
        txtExpDate=_date(),
        chkComp=_chk(),
        chkTPO=_chk(),
        chkSpare=_chk(),
        chkJack=_chk(),
        chkBrace=_chk(),
        text_area_other_items=_box(),
        txtRegNo=_box(),
        txtMakeAndModel=_box(),
        txtChassisNo=_box(),
        txtEngineCC=_box(),
        txtMileage=_box(),
        txtEngineNo=_box(),
        txtEngineCode=_box(),
        txtPaintCode=_box(),
        chkManual=_chk(),
        chkAuto=_chk(),
        chkEmpty=_chk(),
        chkQuarter=_chk(),
        chkHalf=_chk(),
        chkThreeQuarter=_chk(),
        chkFull=_chk(),
        txtInstructions=_box(),
        txtTechNotes=_box(),
        text_area_work_done=_box(),
    )
    form._needs_hydration = lambda data: cls._needs_hydration(form, data)
    return form


def _sample_full_jobcard():
    return {
        "ID": 42,
        "ClientDetails": 10,
        "ClientFullname": "Alice Client",
        "ClientPhone": "0712345678",
        "ClientAddress": "Nairobi",
        "ClientEmail": "alice@example.com",
        "AssignedTechnicianID": 7,
        "AssignedTechnician": "John Tech",
        "CheckedInBy": 3,
        "CheckedInByName": "Jane Staff",
        "JobCardRef": "JC-0042",
        "ReceivedDate": "2026-11-01",
        "DueDate": "2026-11-05",
        "ExpDate": "2026-11-06",
        "Comprehensive": 1,
        "ThirdParty": 0,
        "Spare": 1,
        "Jack": 1,
        "Brace": 1,
        "OtherItems": "Toolkit",
        "RegNo": "KDA 123A",
        "MakeAndModel": "BMW X5",
        "ChassisNo": "WBA123",
        "EngineCC": "3000",
        "Mileage": "85000",
        "EngineNo": "ENG1",
        "EngineCode": "N55",
        "PaintCode": "A52",
        "Manual": 0,
        "Auto": 1,
        "Empty": 0,
        "Quarter": 0,
        "Half": 1,
        "ThreeQuarter": 0,
        "Full": 0,
        "ClientInstruction": "Check brakes",
        "Notes": "Front pads worn",
        "WorkDone": "Replaced pads",
    }


def test_edit_job_card_populates_with_zero_server_calls_when_preloaded(monkeypatch):
    mod, server_call, server_call_s, mod_get_data = _load_edit_jobcard_module(monkeypatch)
    try:
        cls = mod.EditJobCard
        form = _make_edit_jobcard_form(cls)
        cls.populateForm(form, _sample_full_jobcard())

        assert server_call.call_count == 0
        assert server_call_s.call_count == 0
        form.search_keyword_1.set_result.assert_called_once_with({"entry": "John Tech", "ID": 7})
        form.search_keyword_4.set_result.assert_called_once_with({"entry": "Jane Staff", "ID": 3})
        assert form.txt_ClientName.text == "Alice Client"
        assert form.drop_down_selectCustomer.items == [("Alice Client", 10)]
        assert form.drop_down_selectCustomer.selected_value == 10
        assert form.txt_PhoneNo.text == "0712345678"
        assert form.txt_Address.text == "Nairobi"
        assert form.txt_Email.text == "alice@example.com"
        assert form.text_area_work_done.text == "Replaced pads"

        # SearchKeyword lookups use ModGetData caches
        assert cls.getTechnicianName(form) == [{"entry": "John Tech", "ID": 7}]
        assert cls.getStaffDetails(form) == [{"entry": "Jane Staff", "ID": 3}]
        mod_get_data.getTechniciansCached.assert_called_once()
        mod_get_data.getStaffCached.assert_called_once()
        assert server_call.call_count == 0
    finally:
        sys.modules.pop("client_code.EditJobCard", None)


def test_edit_job_card_hydrates_in_single_call_when_minimal_data(monkeypatch):
    mod, server_call, server_call_s, _ = _load_edit_jobcard_module(monkeypatch)
    try:
        cls = mod.EditJobCard
        form = _make_edit_jobcard_form(cls)
        full = _sample_full_jobcard()
        server_call_s.return_value = full

        minimal = {k: v for k, v in full.items() if k not in (
            "AssignedTechnicianID", "AssignedTechnician", "ClientFullname",
            "ClientPhone", "ClientAddress", "ClientEmail", "CheckedInByName", "WorkDone",
        )}
        cls.populateForm(form, minimal)

        assert server_call.call_count == 0
        server_call_s.assert_called_once_with("get_jobcard_form_data", 42)
        assert form.txt_ClientName.text == "Alice Client"
        assert form.text_area_work_done.text == "Replaced pads"
    finally:
        sys.modules.pop("client_code.EditJobCard", None)


def test_jobcard_form_prewarms_and_swaps_edit_jobcard_in_place_without_new_alert(monkeypatch):
    alert_mock = MagicMock()
    notif_mock = MagicMock()
    edit_instance = SimpleNamespace(set_event_handler=MagicMock())
    edit_cls_mock = MagicMock(return_value=edit_instance)
    mod_get_data = _module(
        "client_code.ModGetData",
        getTechniciansCached=MagicMock(),
        getStaffCached=MagicMock(),
    )
    anvil = _module("anvil", Notification=notif_mock, alert=alert_mock)
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module(
        "anvil.server",
        call=MagicMock(),
        call_s=MagicMock(),
        no_loading_indicator=nullcontext(),
    )
    anvil_users = _module("anvil.users")
    modal_el = SimpleNamespace(scrollTop=250)
    anvil_js = _module(
        "anvil.js",
        call=MagicMock(),
        window=SimpleNamespace(
            setTimeout=MagicMock(),
            document=SimpleNamespace(querySelector=MagicMock(return_value=modal_el)),
        ),
    )
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
        "client_code.ModGetData": mod_get_data,
        "client_code.EditJobCard": _module("client_code.EditJobCard", EditJobCard=edit_cls_mock),
        "client_code.JobCardForm._anvil_designer": _module(
            "client_code.JobCardForm._anvil_designer",
            JobCardFormTemplate=type("JobCardFormTemplate", (), {}),
        ),
    }

    target = "client_code.JobCardForm"
    monkeypatch.delitem(sys.modules, target, raising=False)
    for name, m in stubs.items():
        monkeypatch.setitem(sys.modules, name, m)

    mod = importlib.import_module(target)
    try:
        cls = mod.JobCardForm
        data = _sample_full_jobcard()
        form = SimpleNamespace(
            _closed=False,
            _prewarmed_edit_form=None,
            form_data=data,
            txt_JobCardRef=SimpleNamespace(text="JC-0042"),
            clear=MagicMock(),
            add_component=MagicMock(),
            raise_event=MagicMock(),
        )
        form._is_interim_quote_card = lambda: cls._is_interim_quote_card(form)

        # Idle pre-warm builds EditJobCard once and warms technician/staff caches
        cls._prewarm_edit_form(form)
        edit_cls_mock.assert_called_once_with(jobcard_data=data)
        assert form._prewarmed_edit_form is edit_instance
        mod_get_data.getTechniciansCached.assert_called_once()
        mod_get_data.getStaffCached.assert_called_once()

        # Clicking EDIT JOB CARD reuses the pre-warmed instance IN-PLACE with ZERO alert() calls
        cls.btn_EditJobCard_click(form)
        assert edit_cls_mock.call_count == 1  # Not constructed a second time!
        assert alert_mock.call_count == 0     # Existing modal stays open (no close+reopen lag)!
        form.clear.assert_called_once_with()
        form.add_component.assert_called_once_with(edit_instance, full_width_row=True)
        assert modal_el.scrollTop == 0

        # Forwarding x-close-alert from EditJobCard closes outer JobCardForm alert cleanly
        event_name, close_cb = edit_instance.set_event_handler.call_args.args
        assert event_name == "x-close-alert"
        close_cb(value="updated")
        form.raise_event.assert_called_once_with("x-close-alert", value="updated")
    finally:
        sys.modules.pop(target, None)


def test_get_progress_tracker_data_include_modals_single_cursor_and_inline_signature():
    from server_code import invoices

    cursor = MagicMock()
    cursor.fetchone.return_value = (2500.0,)  # SUM(AmountPaid)
    fake_jc = _sample_full_jobcard()
    fake_jc["Status"] = "Ready for Pickup"
    fake_defects = {
        "defects_list": [{"Signature": "data:image/png;base64,cG5nLWJ5dGVz"}],
        "fallback": None,
        "staff_names": [],
    }
    fake_invoices = [
        {"Item": "Pads", "QuantityIssued": 2.0, "Amount": 1500.0, "Status": "Pending"},
        {"Item": "Labour", "QuantityIssued": "", "Amount": 1000.0, "Status": "Paid"},
    ]

    with patch.object(job_cards, "_get_current_user") as auth_mock, \
         patch.object(job_cards, "db_cursor") as db_ctx, \
         patch.object(job_cards, "_fetch_jobcard_form_data", return_value=fake_jc), \
         patch.object(job_cards, "_fetch_defects_form_init_data", return_value=fake_defects), \
         patch.object(quotations, "_fetch_quote_details_by_job_id", return_value=[]), \
         patch.object(quotations, "_fetch_quote_confirmation_details_by_job_id", return_value=[]), \
         patch.object(invoices, "_fetch_invoice_details_by_job_id", return_value=fake_invoices), \
         patch.object(invoices, "_fetch_payments_details", return_value=[{"PaymentID": 1}]):
        db_ctx.return_value.__enter__.return_value = cursor
        res = bma.get_progress_tracker_data(42, include_modals=True)

    assert auth_mock.call_count == 1
    assert db_ctx.call_count == 1
    assert res["job_card"]["ID"] == 42
    assert res["client"]["Fullname"] == "Alice Client"
    assert res["invoice_status"] == "Paid"
    assert res["invoice_total"] == "4,000.00"
    assert res["previous_payment"] == "2,500.00"
    assert res["modals"]["jobcard"] == fake_jc
    assert res["modals"]["invoice"] == fake_invoices


def test_progress_tracker_atomic_hydration_lru_and_post_edit_cache_preservation(monkeypatch):
    mod, server_call, server_call_s, alert_mock = _load_tracker_module(
        monkeypatch, "ProgressTracker", "ProgressTrackerTemplate"
    )
    try:
        cls = mod.ProgressTracker
        form = SimpleNamespace(
            drop_down_JobCardRefDetails=SimpleNamespace(selected_value=42),
            label_MakeAndModel=SimpleNamespace(text=""),
            label_Mileage=SimpleNamespace(text=""),
            label_RegNo=SimpleNamespace(text=""),
            label_date_received=SimpleNamespace(text=""),
            label_Owner=SimpleNamespace(text=""),
            label_Phone=SimpleNamespace(text=""),
            btn_JobCard=SimpleNamespace(enabled=True),
            _modals_cache={},
            _modals_cache_job_id=None,
            _prewarmed_modals={},
            _job_bundles_lru={},
        )
        form.populatePaymentDetails = MagicMock()
        form.set_progress_state = MagicMock()
        form._evict_lru_job = lambda jid=None: cls._evict_lru_job(form, jid)
        form._store_lru_job = lambda jid, t, m, p=None: cls._store_lru_job(form, jid, t, m, p)
        form._invalidate_modals_cache = lambda jid=None: cls._invalidate_modals_cache(form, jid)
        form._apply_tracker_ui = lambda r: cls._apply_tracker_ui(form, r)
        form._priority_modal_keys = lambda s=None: cls._priority_modal_keys(form, s)
        form._schedule_prewarm_modals = MagicMock()
        form._schedule_prewarm_single_modal = MagicMock()
        form._schedule_prefetch_modals = MagicMock()
        form._build_modal_instance = lambda jid, k, d: cls._build_modal_instance(form, jid, k, d)
        form._pop_or_build_modal = lambda jid, k, d: cls._pop_or_build_modal(form, jid, k, d)
        form._get_cached_or_fetch = lambda jid, k, fn: cls._get_cached_or_fetch(form, jid, k, fn)
        form.refresh_selected_job_card = lambda force_server=False: cls.refresh_selected_job_card(form, force_server=force_server)

        payload_42 = {
            "job_card": {"ID": 42, "MakeAndModel": "BMW X5", "Mileage": "85000", "RegNo": "KDA 123A", "ReceivedDate": "2026-11-01", "Status": "Issue Invoice"},
            "client": {"Fullname": "Alice", "Phone": "0712"},
            "invoice_status": "Pending",
            "invoice_total": "4,000.00",
            "previous_payment": 0.0,
            "cancelled_reason": "",
            "modals": {
                "jobcard": {"ID": 42, "JobCardRef": "JC-0042"},
                "defects": {"defects_list": [], "fallback": None, "staff_names": []},
                "quote": [],
                "confirm": [],
                "invoice": [{"Item": "Pads"}],
                "payment": [],
            },
        }
        payload_99 = {
            **payload_42,
            "job_card": {**payload_42["job_card"], "ID": 99, "RegNo": "KDB 999Z"},
            "modals": {**payload_42["modals"], "jobcard": {"ID": 99, "JobCardRef": "JC-0099"}},
        }

        server_call.side_effect = [payload_42, payload_99]

        # 1. Selecting job 42 hydrates BOTH tracker and modals in 1 RPC (zero separate bundle prefetch!)
        cls.refresh_selected_job_card(form)
        server_call.assert_called_once_with("get_progress_tracker_data", 42, True)
        assert server_call_s.call_count == 0
        assert form._modals_cache_job_id == 42
        assert form._modals_cache["invoice"] == [{"Item": "Pads"}]
        # Status-aware priority puts "invoice" first when Status == "Issue Invoice"
        assert cls._priority_modal_keys(form, "Issue Invoice")[0] == "invoice"

        # 2. Switch to job 99 (1 RPC), then switch back to job 42 -> 0 RPCs (served from LRU!)
        form.drop_down_JobCardRefDetails.selected_value = 99
        cls.refresh_selected_job_card(form)
        assert server_call.call_count == 2
        form.drop_down_JobCardRefDetails.selected_value = 42
        cls.refresh_selected_job_card(form)
        assert server_call.call_count == 2  # Zero extra server calls!
        assert form.label_RegNo.text == "KDA 123A"
        assert form._modals_cache_job_id == 42

        # 3. Regression check: EditJobCard returning "updated" after refreshing tracker does NOT wipe _modals_cache!
        alert_mock.return_value = "updated"
        cls.btn_JobCard_click(form)
        assert form._modals_cache_job_id == 42
        assert form._modals_cache != {}
    finally:
        sys.modules.pop("client_code.ProgressTracker", None)


def test_tracker_search_index_and_batch_modals_happy_invalid_unauth_and_invalidation():
    _common.invalidate_lookup_cache()
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [
            (42, "JC-0042", 10, "KDA 123A", "BMW X5", "85000", "2026-11-01", "Ready for Pickup", "Alice Doe", "0711", 4000.0, 9, "Pending", 1500.0, None),
            (41, "JC-0041", 11, "KDB 456B", "BMW X3", "50000", "2026-10-20", "Cancel Jobcard", "Bob Roe", "0722", None, None, None, None, "Client deferred"),
        ],
        [
            (42, "JC-0042", 10, "KDA 123A", "BMW X5", "85000", "2026-11-01", "Ready for Pickup", "Alice Doe", "0711", 4000.0, 9, "Paid", 4000.0, None),
        ],
    ]
    fake_bundle = {
        "jobcard": {"ID": 42, "JobCardRef": "JC-0042"},
        "defects": None,
        "quote": [],
        "confirm": [],
        "invoice": [],
        "payment": [],
    }

    with patch.object(job_cards, "_get_current_user", return_value={"role_id": 1}), \
         patch.object(job_cards, "db_cursor") as db_ctx, \
         patch.object(job_cards, "_fetch_modals_bundle_with_cursor", return_value=fake_bundle) as fetch_modals:
        db_ctx.return_value.__enter__.return_value = cursor

        idx1 = bma.get_tracker_search_index()
        idx2 = bma.get_tracker_search_index()
        assert len(idx1) == 2
        assert idx1 == idx2
        assert db_ctx.call_count == 1  # Served from server TTL cache!
        assert idx1[0]["summary"]["invoice_total"] == "4,000.00"
        assert idx1[0]["summary"]["previous_payment"] == "1,500.00"
        assert idx1[1]["summary"]["invoice_total"] == 0.0
        assert idx1[1]["summary"]["cancelled_reason"] == "Client deferred"

        # Cold/warm search_tracker_jobcards uses cached index + fetches top_modals in 1 DB checkout
        search_res = bma.search_tracker_jobcards("alice")
        assert search_res["items"] == [("Alice Doe - JC-0042", 42)]
        assert 42 in search_res["summaries"]
        assert search_res["top_modals"] == {42: fake_bundle}
        fetch_modals.assert_called_once_with(cursor, 42)

        # Batch modals deduplicates IDs and runs on 1 cursor
        batch = bma.get_progress_tracker_modals_batch([42, 42, 41])
        assert set(batch.keys()) == {42, 41}

        # Publishing jobcards/payments/contacts automatically invalidates tracker_search_index
        with patch.object(_common, "_ensure_realtime_publisher_started"):
            _common.publish_realtime_event("payments", "payment_created", entity_id=42)
        idx3 = bma.get_tracker_search_index()
        assert len(idx3) == 1
        assert idx3[0]["summary"]["invoice_status"] == "Paid"

    # Invalid inputs rejected
    with patch.object(job_cards, "_get_current_user", return_value={"role_id": 1}):
        with pytest.raises(ValueError, match="non-empty string"):
            bma.search_tracker_jobcards("   ")
        with pytest.raises(ValueError, match="list of positive integers"):
            bma.get_progress_tracker_modals_batch("42")
        with pytest.raises(ValueError, match="Invalid job_id"):
            bma.get_progress_tracker_modals_batch([0])

    # Unauthenticated callers rejected
    with patch.object(job_cards, "_get_current_user", side_effect=PermissionError("Authentication required")):
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.get_tracker_search_index()
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.search_tracker_jobcards("JC")
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.get_progress_tracker_modals_batch([42])

    _common.invalidate_lookup_cache()


@pytest.mark.parametrize(
    "module_name,template_name",
    [
        ("ProgressTracker", "ProgressTrackerTemplate"),
        ("ProgressTrackerMobileView", "ProgressTrackerMobileViewTemplate"),
    ],
)
def test_progress_tracker_search_and_dropdown_change_execute_with_zero_blocking_rpcs(
    monkeypatch, module_name, template_name
):
    timeouts = []
    server_call = MagicMock()
    server_call_s = MagicMock(return_value={
        "42": {"jobcard": {"ID": 42}, "defects": None, "quote": [], "confirm": [], "invoice": [], "payment": []},
        "43": {"jobcard": {"ID": 43}, "defects": None, "quote": [], "confirm": [], "invoice": [], "payment": []},
    })

    cached_index = [
        {
            "id": 42 + i,
            "label": f"Alice Doe - JC-00{42 + i}",
            "ref_low": f"jc-00{42 + i}",
            "name_low": "alice doe",
            "summary": {
                "job_card": {
                    "ID": 42 + i,
                    "ClientDetails": 10,
                    "RegNo": f"KDA 10{i}A",
                    "MakeAndModel": f"BMW X{i + 1}",
                    "Mileage": "50000",
                    "ReceivedDate": "2026-11-01",
                    "Status": "In Service",
                },
                "client": {"Fullname": "Alice Doe", "Phone": "0711000000"},
                "invoice_status": None,
                "invoice_total": 0.0,
                "previous_payment": 0.0,
                "cancelled_reason": "",
            },
        }
        for i in range(5)
    ]

    anvil = _module("anvil", Notification=MagicMock(), alert=MagicMock())
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=server_call, call_s=server_call_s, no_loading_indicator=nullcontext())
    anvil_users = _module("anvil.users")
    anvil_js = _module(
        "anvil.js",
        call=MagicMock(),
        get_dom_node=MagicMock(return_value=SimpleNamespace(addEventListener=MagicMock())),
        window=SimpleNamespace(setTimeout=lambda fn, _ms=0: timeouts.append(fn), bmaRealtime=None, Image=None),
    )
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.users = anvil_users
    anvil.js = anvil_js

    mod_get_data = _module(
        "client_code.ModGetData",
        peekTrackerSearchIndexCached=lambda: cached_index,
        getTrackerSearchIndexCached=lambda force_refresh=False: cached_index,
        invalidateTrackerSearchIndex=MagicMock(),
    )

    class FakeTrackerTemplate:
        def init_components(self, **_kw):
            self.txtJobCardRef = SimpleNamespace(text="", focus=MagicMock(), set_event_handler=MagicMock())
            self.drop_down_JobCardRefDetails = SimpleNamespace(items=[], selected_value=None, focus=MagicMock())
            self.btn_SearchCustomer = SimpleNamespace()
            self.btn_JobCard = SimpleNamespace(enabled=True)
            self.btn_Defects = SimpleNamespace(enabled=True)
            self.btn_Quotation = SimpleNamespace(enabled=True)
            self.btn_Confirmed = SimpleNamespace(enabled=True)
            self.btn_Invoice = SimpleNamespace(enabled=True)
            self.btn_Payment = SimpleNamespace(enabled=True)
            self.label_MakeAndModel = SimpleNamespace(text="")
            self.label_Mileage = SimpleNamespace(text="")
            self.label_RegNo = SimpleNamespace(text="")
            self.label_date_received = SimpleNamespace(text="")
            self.label_Owner = SimpleNamespace(text="")
            self.label_Phone = SimpleNamespace(text="")
            self.label_Due = SimpleNamespace(text=0)
            self.label_Paid = SimpleNamespace(text=0)
            self.label_Balance = SimpleNamespace(text=0)
            self.label_Discount = SimpleNamespace(text=0)
            self.text_area_1 = SimpleNamespace(text="", visible=False)
            for lbl_attr in (
                "label_checked_in",
                "label_create_quote",
                "label_confirm_quote",
                "label_in_service",
                "label_verify_task",
                "label_issue_invoice",
                "label_cancelled",
                "label_payment_due",
                "label_payment_done",
                "label_completed",
            ):
                setattr(self, lbl_attr, SimpleNamespace(background="white", foreground="black"))

        def set_event_handler(self, *_a, **_kw):
            pass

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "anvil.js": anvil_js,
        "client_code.ModGetData": mod_get_data,
        f"client_code.{module_name}._anvil_designer": _module(
            f"client_code.{module_name}._anvil_designer",
            **{template_name: FakeTrackerTemplate},
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
        stubs[f"client_code.{sub_mod}"] = _module(f"client_code.{sub_mod}", **{cls_name: MagicMock()})

    target = f"client_code.{module_name}"
    monkeypatch.delitem(sys.modules, target, raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)
    import client_code
    monkeypatch.setattr(client_code, "ModGetData", mod_get_data, raising=False)

    tracker_mod = importlib.import_module(target)
    try:
        cls = getattr(tracker_mod, module_name)
        form = cls()
        timeouts.clear()  # Clear initial index warm timer before testing click latency

        # 1. btn_SearchCustomer_click populates all 5 dropdown results in 0 blocking RPCs!
        form.txtJobCardRef.text = "  alice  "
        form.btn_SearchCustomer_click()
        assert len(form.drop_down_JobCardRefDetails.items) == 5
        assert form.drop_down_JobCardRefDetails.items[0] == ("Alice Doe - JC-0042", 42)
        assert server_call.call_count == 0
        assert server_call_s.call_count == 0  # Speculative batch deferred to setTimeout(..., 0)!

        # 2. Even BEFORE background batch runs, selecting the 5th item (job 46, outside top 3!)
        # renders the ENTIRE tracker UI immediately in 0 blocking RPCs!
        form.drop_down_JobCardRefDetails.selected_value = 46
        form.drop_down_JobCardRefDetails_change()
        assert server_call.call_count == 0
        assert server_call_s.call_count == 0
        assert form.label_Owner.text == "Alice Doe"
        assert form.label_RegNo.text == "KDA 104A"
        assert form.label_MakeAndModel.text == "BMW X5"
        assert form.label_in_service.background == "black"

        # 3. Flushing background timeouts warms top-3 + selected job modals via call_s without blocking UI!
        while timeouts:
            timeouts.pop(0)()
        assert server_call.call_count == 0
        assert server_call_s.call_count >= 1
    finally:
        sys.modules.pop(target, None)
