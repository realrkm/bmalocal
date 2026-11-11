import importlib
import sys
import types
from datetime import datetime
from unittest.mock import MagicMock


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _load_verify_task_module(monkeypatch):
    server = _module(
        "anvil.server",
        call=MagicMock(),
        call_s=MagicMock(
            return_value={
                "time_start": "2026-11-11T08:00:00",
                "time_end": "2026-11-11T09:30:00",
            }
        ),
    )
    anvil = _module("anvil", server=server, BlobMedia=MagicMock())
    anvil.__path__ = []
    anvil_js = _module("anvil.js", call=MagicMock())
    anvil_js.__path__ = []
    stubs = {
        "anvil": anvil,
        "anvil.server": server,
        "anvil.tables": _module("anvil.tables", app_tables=MagicMock()),
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.js": anvil_js,
        "anvil.js.window": _module("anvil.js.window", window=MagicMock()),
        "client_code.VerifyTask._anvil_designer": _module(
            "client_code.VerifyTask._anvil_designer",
            VerifyTaskTemplate=type("VerifyTaskTemplate", (), {}),
        ),
        "client_code.ModGetData": _module("client_code.ModGetData"),
    }
    monkeypatch.delitem(sys.modules, "client_code.VerifyTask", raising=False)
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    return importlib.import_module("client_code.VerifyTask")


def test_loading_saved_verify_times_immediately_updates_worked_hours(monkeypatch):
    module = _load_verify_task_module(monkeypatch)
    form = object.__new__(module.VerifyTask)
    form.date_picker_time_start = types.SimpleNamespace(date=None)
    form.date_picker_time_end = types.SimpleNamespace(date=None)
    form.date_picker_next_service = types.SimpleNamespace(date=None)
    form.txt_next_service_mileage = types.SimpleNamespace(text="")
    form.txt_efficiency = types.SimpleNamespace(text="")
    form.lbl_hrs = types.SimpleNamespace(text="Total hrs:")
    for name in ("chk_torque", "chk_test", "chk_clean", "chk_old", "chk_explain"):
        setattr(form, name, types.SimpleNamespace(checked=False))

    form.load_existing_verify_checklist(42)

    assert form.date_picker_time_start.date == datetime(2026, 11, 11, 8, 0)
    assert form.date_picker_time_end.date == datetime(2026, 11, 11, 9, 30)
    assert form.lbl_hrs.text == "Total hrs: 1.50"


def test_save_uses_datetime_module_to_set_created_timestamp(monkeypatch):
    module = _load_verify_task_module(monkeypatch)
    module.Notification = MagicMock(return_value=types.SimpleNamespace(show=MagicMock()))
    form = object.__new__(module.VerifyTask)
    form.Save = types.SimpleNamespace(enabled=True)
    form.cmbJobCardID = types.SimpleNamespace(selected_value={"ID": 42})
    form.chk_torque = types.SimpleNamespace(checked=True)
    form.chk_test = types.SimpleNamespace(checked=True)
    form.chk_clean = types.SimpleNamespace(checked=True)
    form.chk_old = types.SimpleNamespace(checked=True)
    form.chk_explain = types.SimpleNamespace(checked=True)
    form.date_picker_next_service = types.SimpleNamespace(date=datetime(2026, 12, 1))
    form.txt_next_service_mileage = types.SimpleNamespace(text="50000")
    form.date_picker_time_start = types.SimpleNamespace(date=datetime(2026, 11, 11, 8))
    form.date_picker_time_end = types.SimpleNamespace(date=datetime(2026, 11, 11, 9))
    form.txt_efficiency = types.SimpleNamespace(text="90%")
    form.txtRemarks = types.SimpleNamespace(text="Verified")
    form.signature_form_1 = types.SimpleNamespace(get_signature_image=MagicMock(return_value="signature"))
    form.cmbWorkflow = types.SimpleNamespace(selected_value="Completed")
    form.btn_Close_click = MagicMock()

    form.Save_click()

    save_call = module.anvil.server.call.call_args
    assert save_call.args[0] == "saveConfirmationDetails"
    assert save_call.args[1] == 42
    assert isinstance(save_call.args[4], datetime)
