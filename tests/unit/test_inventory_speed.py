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


def test_inventory_caches_and_prewarms_all_three_subforms_for_instant_switching(monkeypatch):
    class FakeButton:
        def __init__(self, text):
            self.text = text
            self.visible = False
            self.enabled = False
            self.background = "#0056D6"
            self.foreground = "white"

    anp_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="anp"))
    ams_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="ams"))
    st_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="st"))

    anvil = _module("anvil", Button=FakeButton)
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=MagicMock(), call_s=MagicMock(), no_loading_indicator=nullcontext())
    anvil_users = _module("anvil.users")
    timeouts = []
    anvil_js = _module(
        "anvil.js",
        call=MagicMock(),
        get_dom_node=MagicMock(return_value=SimpleNamespace(addEventListener=MagicMock())),
        window=SimpleNamespace(setTimeout=lambda fn, _ms=0: timeouts.append(fn)),
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
        "client_code.AddNewParts": _module("client_code.AddNewParts", AddNewParts=anp_cls),
        "client_code.AddMoreStock": _module("client_code.AddMoreStock", AddMoreStock=ams_cls),
        "client_code.StockTake": _module("client_code.StockTake", StockTake=st_cls),
        "client_code.Inventory._anvil_designer": _module(
            "client_code.Inventory._anvil_designer",
            InventoryTemplate=type("InventoryTemplate", (), {}),
        ),
    }

    target = "client_code.Inventory"
    monkeypatch.delitem(sys.modules, target, raising=False)
    for name, m in stubs.items():
        monkeypatch.setitem(sys.modules, name, m)

    mod = importlib.import_module(target)
    try:
        cls = mod.Inventory
        b_anp = FakeButton("ADD NEW PARTS")
        b_ams = FakeButton("ADD MORE STOCK")
        b_st = FakeButton("STOCK TAKING")
        mounted = []

        form = SimpleNamespace(
            permissions={
                "INVENTORY": {
                    "main": True,
                    "subs": {
                        "Add New Parts": True,
                        "Add More Stock": True,
                        "Stock Taking": True,
                    },
                }
            },
            _initial_subform_loaded=False,
            _first_visible=None,
            _authorized_keys=[],
            _subforms={},
            _active_key=None,
            btn_AddNewParts=b_anp,
            btn_AddMoreStock=b_ams,
            btn_StockTaking=b_st,
            card_1=SimpleNamespace(get_components=lambda: [b_anp, b_ams, b_st]),
            card_2=SimpleNamespace(
                clear=lambda: mounted.clear(),
                add_component=lambda c, **_kw: mounted.append(c),
                get_components=lambda: list(mounted),
            ),
        )
        form._build_subform = lambda k: cls._build_subform(form, k)
        form._get_or_create_subform = lambda k: cls._get_or_create_subform(form, k)
        form._prewarm_single_subform = lambda k: cls._prewarm_single_subform(form, k)
        form._schedule_prewarm_subforms = lambda: cls._schedule_prewarm_subforms(form)
        form._activate_subform = lambda k, b, lbl, full_width=False: cls._activate_subform(form, k, b, lbl, full_width=full_width)
        form.highlight_active_button = lambda t: cls.highlight_active_button(form, t)
        form.show_clicked_button = lambda n: cls.show_clicked_button(form, n)
        form.btn_AddNewParts_click = lambda: cls.btn_AddNewParts_click(form)
        form.btn_AddMoreStock_click = lambda: cls.btn_AddMoreStock_click(form)
        form.btn_StockTaking_click = lambda: cls.btn_StockTaking_click(form)

        cls.apply_permissions(form)
        cls.form_show(form)

        while timeouts:
            fn = timeouts.pop(0)
            fn()

        assert anp_cls.call_count == 1
        assert ams_cls.call_count == 1
        assert st_cls.call_count == 1
        assert len(form._subforms) == 3

        # Switching across all 3 tabs reuses pre-built instances with ZERO new instantiations
        cls.btn_AddMoreStock_click(form)
        assert mounted[-1].name == "ams"
        cls.btn_StockTaking_click(form)
        assert mounted[-1].name == "st"
        assert b_st.background == "#000000"
        assert b_ams.background == "#0056D6"
        cls.btn_AddNewParts_click(form)
        assert mounted[-1].name == "anp"

        assert anp_cls.call_count == 1
        assert ams_cls.call_count == 1
        assert st_cls.call_count == 1
    finally:
        sys.modules.pop(target, None)


def test_stocktake_prewarm_is_side_effect_free_and_shows_tip_only_on_show(monkeypatch):
    alert_mock = MagicMock()
    tip_cls = MagicMock(return_value=SimpleNamespace(name="tip"))
    timeouts = []
    win = SimpleNamespace(
        display_result=None,
        setTimeout=lambda fn, _ms=0: timeouts.append(fn),
        stopScanner=MagicMock(),
    )

    anvil = _module("anvil", alert=alert_mock, Notification=MagicMock(), confirm=MagicMock())
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=MagicMock(), call_s=MagicMock())
    anvil_users = _module("anvil.users")
    anvil_js = _module("anvil.js", window=win, report_exceptions=lambda fn: fn)
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
        "client_code.StockTakingTip": _module("client_code.StockTakingTip", StockTakingTip=tip_cls),
        "client_code.StockTake._anvil_designer": _module(
            "client_code.StockTake._anvil_designer",
            StockTakeTemplate=type("StockTakeTemplate", (), {"init_components": lambda self, **_p: None}),
        ),
    }

    target = "client_code.StockTake"
    monkeypatch.delitem(sys.modules, target, raising=False)
    for name, m in stubs.items():
        monkeypatch.setitem(sys.modules, name, m)

    mod = importlib.import_module(target)
    try:
        cls = mod.StockTake
        inst = object.__new__(cls)
        inst.repeating_panel_1 = SimpleNamespace(items=None)
        inst.txt_BarcodePartNo = SimpleNamespace(text="")
        inst.set_event_handler = MagicMock()
        cls.__init__(inst)

        # Drain background tip pre-warm — must NOT pop alert() or touch window.display_result!
        while timeouts:
            timeouts.pop(0)()
        assert alert_mock.call_count == 0
        assert win.display_result is None
        assert tip_cls.call_count == 1

        # Showing StockTake attaches scanner callback and opens the pre-warmed tip once
        cls.form_show(inst)
        while timeouts:
            timeouts.pop(0)()
        assert win.display_result is not None
        assert alert_mock.call_count == 1
        assert tip_cls.call_count == 1  # Reused pre-warmed tip!

        # Re-showing StockTake on subsequent tab switches does not re-nag with tip
        cls.form_show(inst)
        while timeouts:
            timeouts.pop(0)()
        assert alert_mock.call_count == 1
    finally:
        sys.modules.pop(target, None)
