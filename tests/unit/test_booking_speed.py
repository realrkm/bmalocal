import datetime
import importlib
import sys
import types
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import server_code.BMALocal as bma
from server_code import _common, bookings


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def test_booking_server_index_friendly_sql_cache_invalidation_and_unauth():
    _common.invalidate_lookup_cache()
    dt = datetime.datetime(2026, 12, 1, 9, 30)
    cursor = MagicMock()
    cursor.description = [
        ("Fullname",),
        ("RegNo",),
        ("Period",),
        ("Details",),
        ("Phone",),
        ("ID",),
    ]
    cursor.fetchall.side_effect = [
        [("Alice Doe", "KDA 111A", dt, "Major Service", "0711000000", 15)],
        [("Alice Doe", "KDA 111A", dt, "Major Service", "0711000000", 15), ("Bob Roe", "KDB 222B", dt, "Brakes", "0722000000", 16)],
    ]
    cursor.lastrowid = 16

    with patch.object(bookings, "_get_current_user", return_value={"role_id": 1}), \
         patch.object(bookings, "publish_realtime_event") as pub_mock, \
         patch.object(bookings, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor

        first = bma.getBookingDetails()
        second = bma.getBookingDetails()
        assert first == [
            {
                "No": 1,
                "Fullname": "Alice Doe",
                "RegNo": "KDA 111A",
                "Period": dt,
                "FormattedSchedule": "01-12-2026 at 09:30 AM",
                "Details": "Major Service",
                "Phone": "0711000000",
                "ID": 15,
            }
        ]
        assert second == first
        # Served from server TTL cache -> 1 DB checkout!
        assert db_ctx.call_count == 1

        executed_sql = cursor.execute.call_args.args[0]
        assert "DATE(b.Period)" not in executed_sql
        assert "b.Period >= CURDATE()" in executed_sql

        # Saving a booking invalidates cache and publishes realtime event
        assert bma.saveBookingDetails(10, "KDB 222B", dt, "Brakes") is True
        pub_mock.assert_any_call("bookings", "booking_created", entity_id=16)

        refreshed = bma.getBookingDetails()
        assert len(refreshed) == 2

        # Marking sent invalidates cache and publishes realtime event
        bma.updateAppointmentSent(15)
        pub_mock.assert_any_call("bookings", "booking_sent", entity_id=15)

    with patch.object(bookings, "_get_current_user", side_effect=PermissionError("Authentication required")):
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.getBookingDetails()
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.saveBookingDetails(10, "KDA 111A", dt, "Service")
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.updateAppointmentSent(15)

    _common.invalidate_lookup_cache()


def test_booking_form_mounts_with_zero_rpcs_and_speculatively_warms_customer_regs(monkeypatch):
    timeouts = []
    server_call = MagicMock()
    server_call_s = MagicMock(return_value=["KDA 111A", "KDC 333C"])

    anvil = _module("anvil", Notification=MagicMock(), alert=MagicMock())
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=server_call, call_s=server_call_s, no_loading_indicator=nullcontext())
    anvil_users = _module("anvil.users")
    anvil_js = _module(
        "anvil.js",
        call=MagicMock(),
        window=SimpleNamespace(setTimeout=lambda fn, _ms=0: timeouts.append(fn), bmaRealtime=None),
    )
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.users = anvil_users
    anvil.js = anvil_js

    cached_bookings = [
        {"No": 1, "ID": 15, "Fullname": "Alice Doe", "RegNo": "KDA 111A", "FormattedSchedule": "01-12-2026 at 09:30 AM"}
    ]
    cached_clients = [
        {"ID": 10, "Fullname": "Alice Doe", "Phone": "0711000000"},
        {"ID": 20, "Fullname": "Bob Roe", "Phone": "0722000000"},
    ]
    mod_get_data = _module(
        "client_code.ModGetData",
        peekBookingsCached=lambda: cached_bookings,
        getBookingsCached=lambda force_refresh=False: cached_bookings,
        peekClientReportCached=lambda: cached_clients,
    )

    class FakeBookingTemplate:
        def init_components(self, **_kw):
            self.repeating_panel_1 = SimpleNamespace(items=[], set_event_handler=MagicMock())
            self.txt_ClientName = SimpleNamespace(text="")
            self.drop_down_selectCustomer = SimpleNamespace(items=[], selected_value=None)
            self.drop_down_car_reg = SimpleNamespace(items=[], selected_value=None)
            self.date_picker_period = SimpleNamespace(date=None)
            self.txt_area_details = SimpleNamespace(text="")

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
        "client_code.Booking._anvil_designer": _module(
            "client_code.Booking._anvil_designer",
            BookingTemplate=FakeBookingTemplate,
        ),
    }

    monkeypatch.delitem(sys.modules, "client_code.Booking", raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)
    import client_code
    monkeypatch.setattr(client_code, "ModGetData", mod_get_data, raising=False)

    booking_mod = importlib.import_module("client_code.Booking")
    try:
        form = booking_mod.Booking()

        # Mounted with 0 server calls and 0 deferred timeouts when cache is warm!
        assert server_call.call_count == 0
        assert server_call_s.call_count == 0
        assert timeouts == []
        assert form.repeating_panel_1.items == cached_bookings

        # Customer search resolves in RAM (0 blocking calls) and schedules speculative reg warm for result[0]
        form.txt_ClientName.text = "alice"
        form.btn_SearchCustomer_click()
        assert form.drop_down_selectCustomer.items == [("Alice Doe", 10)]
        assert server_call.call_count == 0
        assert len(timeouts) == 1

        # Background 0ms slice warms Alice's car registrations before dropdown selection!
        timeouts.pop(0)()
        server_call_s.assert_called_once_with("getCarRegNoFromClientID", 10)

        # Selecting Alice populates car registrations in 0ms with ZERO click-time RPCs!
        form.drop_down_selectCustomer.selected_value = 10
        form.drop_down_selectCustomer_change()
        assert form.drop_down_car_reg.items == ["KDA 111A", "KDC 333C"]
        assert server_call.call_count == 0
    finally:
        sys.modules.pop("client_code.Booking", None)


def test_mod_navigation_prewarms_and_reuses_booking_instance(monkeypatch):
    booking_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="booking_form"))
    anvil = _module("anvil")
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server")
    anvil_users = _module("anvil.users")
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.users = anvil_users

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "client_code.Booking": _module("client_code.Booking", Booking=booking_cls),
    }

    monkeypatch.delitem(sys.modules, "client_code.ModNavigation", raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)

    nav = importlib.import_module("client_code.ModNavigation")
    try:
        loaded = []
        nav.home_form = SimpleNamespace(load_component=lambda c: loaded.append(c))
        nav.go_Booking()
        nav.go_Booking()
        assert booking_cls.call_count == 1
        assert len(loaded) == 2
        assert loaded[0] is loaded[1]

        nav.clear_cached_forms()
        nav.go_Booking()
        assert booking_cls.call_count == 2
    finally:
        sys.modules.pop("client_code.ModNavigation", None)
