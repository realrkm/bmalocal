import importlib
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock


class _RepeatingPanel:
    def __init__(self):
        self.event_handlers = {}
        self.items = None

    def set_event_handler(self, event_name, handler):
        self.event_handlers[event_name] = handler

    def raise_event(self, event_name):
        self.event_handlers[event_name](sender=self)


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _load_booking_row(monkeypatch):
    server_call = MagicMock()
    repeating_panel = _RepeatingPanel()
    js_window = SimpleNamespace(
        encodeURIComponent=MagicMock(return_value="encoded message"),
        open=MagicMock(),
    )
    js_call = MagicMock()
    anvil = _module("anvil")
    anvil.__path__ = []
    anvil_server = _module("anvil.server", call=server_call)
    anvil_users = _module("anvil.users")
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_js = _module("anvil.js", call=js_call, window=js_window)

    class BookingTemplate:
        def init_components(self, **properties):
            self.repeating_panel_1 = repeating_panel

    anvil.server = anvil_server
    anvil.users = anvil_users
    anvil.tables = anvil_tables
    anvil.js = anvil_js

    stubs = {
        "anvil": anvil,
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.js": anvil_js,
        "client_code.Booking._anvil_designer": _module(
            "client_code.Booking._anvil_designer",
            BookingTemplate=BookingTemplate,
        ),
        "client_code.Booking.RowTemplate24._anvil_designer": _module(
            "client_code.Booking.RowTemplate24._anvil_designer",
            RowTemplate24Template=type("RowTemplate24Template", (), {}),
        ),
    }
    for name in ("client_code.Booking.RowTemplate24", "client_code.Booking"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    row_module = importlib.import_module("client_code.Booking.RowTemplate24")
    booking_module = importlib.import_module("client_code.Booking")
    return row_module, booking_module, server_call, js_window, js_call, repeating_panel


def test_sending_whatsapp_reminder_requests_booking_list_refresh(monkeypatch):
    (
        row_module,
        booking_module,
        server_call,
        js_window,
        js_call,
        repeating_panel,
    ) = _load_booking_row(monkeypatch)

    booking = object.__new__(booking_module.Booking)
    booking.__init__()
    assert repeating_panel.event_handlers["x-refresh-bookings"] == booking.refresh_data_grid
    js_call.assert_called_once_with("replaceBanner")

    row = object.__new__(row_module.RowTemplate24)
    row.item = {
        "Phone": "+1 (555) 010-0100",
        "Fullname": "Test Customer",
        "RegNo": "TEST-123",
        "FormattedSchedule": "18-11-2026 at 01:00 PM",
        "ID": 42,
    }
    row.parent = repeating_panel

    row.btn_SendWhatsAppMessage_click()

    assert [call.args for call in server_call.call_args_list] == [
        ("getBookingDetails",),
        ("updateAppointmentSent", 42),
        ("getBookingDetails",),
    ]
    js_window.open.assert_called_once_with(
        "whatsapp://send?phone=15550100100&text=encoded message",
        "_blank",
    )
