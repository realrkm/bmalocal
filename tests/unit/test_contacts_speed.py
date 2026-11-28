import importlib
import sys
import types
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import server_code.BMALocal as bma
from server_code import _common, people


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def test_toolkits_server_cache_invalidation_realtime_and_unauth():
    _common.invalidate_lookup_cache()
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [(1, "Box A", 5000.0), (2, "Box B", 7500.0)],
        [(2, "Box B", 7500.0)],
        [(1, "Box A", 5000.0), (2, "Box B", 8000.0), (3, "Box C", 9000.0)],
    ]
    cursor.lastrowid = 3

    with patch.object(people, "_get_current_user", return_value={"role_id": 1}), \
         patch.object(people, "publish_realtime_event") as pub_mock, \
         patch.object(people, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor

        first = bma.get_toolkits(None)
        second = bma.get_toolkits(None)
        assert first == [
            {"ID": 1, "ToolkitName": "Box A", "Cost": 5000.0},
            {"ID": 2, "ToolkitName": "Box B", "Cost": 7500.0},
        ]
        assert second == first
        # Second call served from server TTL cache -> 1 DB checkout!
        assert db_ctx.call_count == 1

        by_id = bma.get_toolkits(2)
        assert by_id == [{"ID": 2, "ToolkitName": "Box B", "Cost": 7500.0}]
        assert db_ctx.call_count == 2

        bma.save_toolkit_data("Box C", 9000.0)
        pub_mock.assert_any_call("contacts", "toolkit_created", entity_id=3)

        bma.update_toolkit_data("Box B", 8000.0, 2)
        pub_mock.assert_any_call("contacts", "toolkit_updated", entity_id=2)

        # Cache invalidated after save/update -> fresh DB query runs
        refreshed = bma.get_toolkits(None)
        assert len(refreshed) == 3

    with patch.object(people, "_get_current_user", side_effect=PermissionError("Authentication required")):
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.get_toolkits(None)
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.save_toolkit_data("Box X", 100)
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.update_toolkit_data("Box X", 100, 1)

    _common.invalidate_lookup_cache()


def test_contacts_hub_prewarms_and_switches_all_3_subforms_with_zero_rebuilds(monkeypatch):
    class FakeButton:
        def __init__(self, text):
            self.text = text
            self.visible = False
            self.enabled = False
            self.background = "#0056D6"
            self.foreground = "white"

    timeouts = []
    warm_calls = []
    client_cls = MagicMock(side_effect=lambda: SimpleNamespace(tab="CLIENTS"))
    tech_cls = MagicMock(side_effect=lambda: SimpleNamespace(tab="TECHNICIANS", refresh_toolkits=MagicMock()))
    staff_cls = MagicMock(side_effect=lambda: SimpleNamespace(tab="STAFF"))

    anvil = _module("anvil", Button=FakeButton)
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=MagicMock(), call_s=MagicMock(), no_loading_indicator=nullcontext())
    anvil_users = _module("anvil.users")
    anvil_js = _module(
        "anvil.js",
        call=MagicMock(),
        get_dom_node=MagicMock(return_value=SimpleNamespace(addEventListener=MagicMock())),
        window=SimpleNamespace(setTimeout=lambda fn, _ms=0: timeouts.append(fn), bmaRealtime=None),
    )
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.users = anvil_users
    anvil.js = anvil_js

    class FakeContactsTemplate:
        def init_components(self, **_kw):
            self.btn_Client = FakeButton("CLIENTS")
            self.btn_Technician = FakeButton("TECHNICIANS")
            self.btn_Staff = FakeButton("STAFF")
            btns = [self.btn_Client, self.btn_Technician, self.btn_Staff]
            self.card_1 = SimpleNamespace(get_components=lambda: btns)
            mounted = []
            self.card_2 = SimpleNamespace(
                visible=True,
                clear=lambda: mounted.clear(),
                add_component=lambda c, **_k: mounted.append(c),
                get_components=lambda: list(mounted),
            )

        def set_event_handler(self, *_a, **_kw):
            pass

    mod_get_data = _module(
        "client_code.ModGetData",
        warmContactsCaches=lambda perms=None: warm_calls.append(perms),
    )

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "anvil.js": anvil_js,
        "client_code.ModGetData": mod_get_data,
        "client_code.Client": _module("client_code.Client", Client=client_cls),
        "client_code.Tehnicians": _module("client_code.Tehnicians", Tehnicians=tech_cls),
        "client_code.Staffs": _module("client_code.Staffs", Staffs=staff_cls),
        "client_code.Contacts._anvil_designer": _module(
            "client_code.Contacts._anvil_designer",
            ContactsTemplate=FakeContactsTemplate,
        ),
    }

    monkeypatch.delitem(sys.modules, "client_code.Contacts", raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)
    import client_code
    monkeypatch.setattr(client_code, "ModGetData", mod_get_data, raising=False)

    contacts_mod = importlib.import_module("client_code.Contacts")
    try:
        perms = {
            "CONTACT": {
                "main": True,
                "subs": {
                    "Clients": True,
                    "Technicians": True,
                    "Staff": True,
                },
            }
        }
        form = contacts_mod.Contacts(perms)
        form.form_show()
        while timeouts:
            timeouts.pop(0)()

        assert len(warm_calls) == 1
        assert client_cls.call_count == 1
        assert tech_cls.call_count == 1
        assert staff_cls.call_count == 1
        assert form.card_2.get_components()[-1].tab == "CLIENTS"

        # Switching across Clients, Technicians, and Staff reuses cached instances with 0 rebuilds!
        for _ in range(2):
            form.btn_Technician_click()
            assert form.card_2.get_components()[-1].tab == "TECHNICIANS"
            form.btn_Staff_click()
            assert form.card_2.get_components()[-1].tab == "STAFF"
            form.btn_Client_click()
            assert form.card_2.get_components()[-1].tab == "CLIENTS"

        assert client_cls.call_count == 1
        assert tech_cls.call_count == 1
        assert staff_cls.call_count == 1
    finally:
        sys.modules.pop("client_code.Contacts", None)


def test_technicians_and_toolkit_modals_use_warm_cache_with_zero_rpcs(monkeypatch):
    timeouts = []
    server_call = MagicMock()
    server_call_s = MagicMock()

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
        window=SimpleNamespace(setTimeout=lambda fn, _ms=0: timeouts.append(fn), bmaRealtime=None),
    )
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.users = anvil_users
    anvil.js = anvil_js

    cached_toolkits = [
        {"ID": 1, "ToolkitName": "Box A", "Cost": 5000.0},
        {"ID": 2, "ToolkitName": "Box B", "Cost": 7500.0},
    ]
    mod_get_data = _module(
        "client_code.ModGetData",
        peekToolkitsCached=lambda: cached_toolkits,
        getToolkitsCached=lambda force_refresh=False: cached_toolkits,
    )

    class FakeTechTemplate:
        def init_components(self, **_kw):
            self.dropdown_toolkits = SimpleNamespace(items=[], selected_value=cached_toolkits[0])
            self.txt_name = SimpleNamespace(text="JOHN", focus=lambda: None)
            self.txt_phone = SimpleNamespace(text="0700")
            self.btn_SaveAndNew = SimpleNamespace(enabled=False)
            self.btn_EditTechnician = SimpleNamespace()
            self.btn_Toolkit = SimpleNamespace()

    class FakeEditTechTemplate:
        def init_components(self, **_kw):
            self.dropdown_toolkits = SimpleNamespace(items=[], selected_value=None)
            self.txt_technicianName = SimpleNamespace(text="", focus=lambda: None)
            self.drop_down_selectName = SimpleNamespace(items=[], selected_value=7)
            self.txt_name = SimpleNamespace(text="")
            self.txt_phone = SimpleNamespace(text="")
            self.drop_down_archived = SimpleNamespace(selected_value=None)

    class FakeEditToolkitTemplate:
        def init_components(self, **_kw):
            self.search_keyword_1 = SimpleNamespace(
                text_box_search=SimpleNamespace(placeholder="", focus=lambda: None),
                selected_result=None,
                set_event_handler=lambda *_a, **_k: None,
            )
            self.txt_name = SimpleNamespace(text="")
            self.txt_amount = SimpleNamespace(text="")

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "anvil.js": anvil_js,
        "client_code.ModGetData": mod_get_data,
        "client_code.Tehnicians._anvil_designer": _module(
            "client_code.Tehnicians._anvil_designer",
            TehniciansTemplate=FakeTechTemplate,
        ),
        "client_code.EditTechnician._anvil_designer": _module(
            "client_code.EditTechnician._anvil_designer",
            EditTechnicianTemplate=FakeEditTechTemplate,
        ),
        "client_code.EditToolkit._anvil_designer": _module(
            "client_code.EditToolkit._anvil_designer",
            EditToolkitTemplate=FakeEditToolkitTemplate,
        ),
    }

    targets = ("client_code.Tehnicians", "client_code.EditTechnician", "client_code.EditToolkit")
    for mod_name in targets:
        monkeypatch.delitem(sys.modules, mod_name, raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)
    import client_code
    monkeypatch.setattr(client_code, "ModGetData", mod_get_data, raising=False)

    tech_mod = importlib.import_module("client_code.Tehnicians")
    edit_tech_mod = importlib.import_module("client_code.EditTechnician")
    edit_tk_mod = importlib.import_module("client_code.EditToolkit")
    try:
        tech_form = tech_mod.Tehnicians()
        edit_tech_form = edit_tech_mod.EditTechnician()
        edit_tk_form = edit_tk_mod.EditToolkit()

        # Zero blocking RPCs and zero deferred setTimeouts during initialization!
        assert server_call.call_count == 0
        assert server_call_s.call_count == 0
        assert timeouts == []
        assert len(tech_form.dropdown_toolkits.items) == 2
        assert len(edit_tech_form.dropdown_toolkits.items) == 2

        # clear_form_fields resets dropdown selection without making a server call
        tech_form.clear_form_fields()
        assert tech_form.dropdown_toolkits.selected_value is None
        assert server_call.call_count == 0

        # EditToolkit resolves both search keys and selected toolkit Cost in RAM (0 RPCs)
        assert edit_tk_form.getToolkit() == [
            {"entry": "Box A", "ID": 1},
            {"entry": "Box B", "ID": 2},
        ]
        edit_tk_form.populateClientDetails({"ID": 2})
        assert edit_tk_form.txt_name.text == "Box B"
        assert edit_tk_form.txt_amount.text == 7500.0
        assert server_call.call_count == 0

        # Selecting a technician in EditTechnician resolves ToolkitID in RAM (only 1 RPC, not 2!)
        server_call.return_value = [
            {"ID": 7, "Fullname": "JOHN TECH", "Phone": "0711", "ToolkitID": 2, "Active": "No"}
        ]
        edit_tech_form.drop_down_selectName_change()
        server_call.assert_called_once_with("get_technician_details", 7)
        assert server_call_s.call_count == 0
        assert edit_tech_form.dropdown_toolkits.selected_value == cached_toolkits[1]
    finally:
        for mod_name in targets:
            sys.modules.pop(mod_name, None)
