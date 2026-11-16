import importlib
import sys
import types
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _load_mod_get_data(monkeypatch):
    notification_factory = MagicMock()
    now = MagicMock(return_value=10_000)
    set_timeout = MagicMock()
    window = SimpleNamespace(
        Date=SimpleNamespace(now=now),
        setTimeout=set_timeout,
        location=SimpleNamespace(reload=MagicMock()),
    )
    anvil = _module("anvil", Notification=notification_factory)
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module(
        "anvil.server",
        UplinkDisconnectedError=type("UplinkDisconnectedError", (Exception,), {}),
        SessionExpiredError=type("SessionExpiredError", (Exception,), {}),
        AppOfflineError=type("AppOfflineError", (Exception,), {}),
    )
    anvil_users = _module("anvil.users")
    anvil_js = _module("anvil.js", window=window)
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
    }
    target_module = "client_code.ModGetData"
    monkeypatch.delitem(sys.modules, target_module, raising=False)
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    module = importlib.import_module(target_module)
    monkeypatch.setitem(sys.modules, target_module, module)
    return module, notification_factory, set_timeout, window


def test_app_offline_error_is_shown_as_a_throttled_notification(monkeypatch):
    mod_get_data, notification_factory, set_timeout, _ = _load_mod_get_data(monkeypatch)
    offline_error = mod_get_data.anvil.server.AppOfflineError()

    mod_get_data.handle_server_errors(offline_error)
    mod_get_data.handle_server_errors(offline_error)

    notification_factory.assert_called_once_with(
        "Please ensure the server is up and running.",
        title="Lost connection",
        style="danger",
        timeout=5,
    )
    notification_factory.return_value.show.assert_called_once()
    set_timeout.assert_called_once()


def test_server_error_messages_are_preserved(monkeypatch):
    mod_get_data, notification_factory, _, _ = _load_mod_get_data(monkeypatch)
    mod_get_data.handle_server_errors(RuntimeError("Unexpected response"))

    notification_factory.assert_called_once_with(
        "Unexpected response",
        title="Issue Detected",
        style="danger",
        timeout=5,
    )
    notification_factory.return_value.show.assert_called_once()


def test_expired_session_still_reloads_without_a_notification(monkeypatch):
    mod_get_data, notification_factory, _, window = _load_mod_get_data(monkeypatch)
    mod_get_data.handle_server_errors(mod_get_data.anvil.server.SessionExpiredError())

    window.location.reload.assert_called_once()
    notification_factory.assert_not_called()


def test_main_poll_shows_the_latest_job_card_notification(monkeypatch):
    notification_factory = MagicMock()
    notification_data = {
        "notifications": [
            {"jobcard": "JC-100", "message": "First update"},
            {"jobcard": "JC-200", "message": "Latest update"},
        ],
        "incomplete_defects": [],
        "technician_portal": [],
        "pricing_alert": [],
    }
    anvil_server = _module(
        "anvil.server",
        call_s=MagicMock(return_value=notification_data),
        no_loading_indicator=nullcontext(),
    )
    anvil_users = _module("anvil.users")
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_js_window = _module(
        "anvil.js.window",
        navigator=SimpleNamespace(userAgent="test"),
        setTimeout=MagicMock(),
        document=SimpleNamespace(hidden=False),
    )
    anvil_js = _module("anvil.js", window=anvil_js_window)
    anvil = _module(
        "anvil",
        Notification=notification_factory,
        set_default_error_handling=MagicMock(),
    )
    anvil.__path__ = []
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
        "anvil.js.window": anvil_js_window,
        "client_code.Main._anvil_designer": _module(
            "client_code.Main._anvil_designer",
            MainTemplate=type("MainTemplate", (), {}),
        ),
        "client_code.ModNavigation": _module("client_code.ModNavigation"),
        "client_code.ModGetData": _module(
            "client_code.ModGetData", handle_server_errors=MagicMock()
        ),
        "client_code.NotificationsAndAlerts": _module(
            "client_code.NotificationsAndAlerts",
            NotificationsAndAlerts=type("NotificationsAndAlerts", (), {}),
        ),
        "client_code.WalkieTalkieChat": _module(
            "client_code.WalkieTalkieChat",
            WalkieTalkieChat=type("WalkieTalkieChat", (), {}),
        ),
    }
    target_module = "client_code.Main"
    monkeypatch.delitem(sys.modules, target_module, raising=False)
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    main_module = importlib.import_module(target_module)
    monkeypatch.setitem(sys.modules, target_module, main_module)
    form = object.__new__(main_module.Main)
    form.polling_active = True
    form.poll_running = False
    form.user = {"email": "staff@example.com"}
    form.link_1 = SimpleNamespace()

    form.run_notification_poll()

    notification_factory.assert_called_once_with(
        "JC-200 - Latest update",
        style="warning",
        timeout=3,
    )
    notification_factory.return_value.show.assert_called_once()
