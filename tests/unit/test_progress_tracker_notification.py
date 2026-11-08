import importlib
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def test_inspection_button_stays_disabled_until_notification_timeout(monkeypatch):
    timer = MagicMock()
    notification = MagicMock()

    anvil = _module("anvil", Notification=MagicMock(return_value=notification))
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server")
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
        "client_code.ProgressTracker._anvil_designer": _module(
            "client_code.ProgressTracker._anvil_designer",
            ProgressTrackerTemplate=type("ProgressTrackerTemplate", (), {}),
        ),
    }

    imported_forms = (
        ("JobCardForm", "JobCardForm"),
        ("DefectsForm", "DefectsForm"),
        ("QuoteForm", "QuoteForm"),
        ("ConfirmForm", "ConfirmForm"),
        ("InvoiceForm", "InvoiceForm"),
        ("PaymentForm", "PaymentForm"),
        ("VehicleInspectionChecklist", "VehicleInspectionChecklist"),
    )
    for module_name, class_name in imported_forms:
        stubs[f"client_code.{module_name}"] = _module(
            f"client_code.{module_name}", **{class_name: type(class_name, (), {})}
        )

    target_module = "client_code.ProgressTracker"
    monkeypatch.delitem(sys.modules, target_module, raising=False)
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    try:
        progress_tracker = importlib.import_module(target_module)
        form = SimpleNamespace(
            btn_ViewInspection=SimpleNamespace(enabled=True),
            drop_down_JobCardRefDetails=SimpleNamespace(selected_value=None),
        )

        progress_tracker.ProgressTracker.btn_ViewInspection_click(form)

        assert form.btn_ViewInspection.enabled is False
        timer.assert_called_once()
        callback, delay_ms = timer.call_args.args
        assert delay_ms == 3000
        callback()
        assert form.btn_ViewInspection.enabled is True
        notification.show.assert_called_once()
    finally:
        sys.modules.pop(target_module, None)
