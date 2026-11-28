import importlib
import sys
import types
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import server_code.BMALocal as bma
from server_code import inventory


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def test_save_repair_priorities_batch_happy_invalid_and_unauth():
    cursor = MagicMock()
    items = [
        {"name": "Brake Pads", "number": "BP-1", "quantity": 2, "amount": 3500.0, "priority": "Urgent"},
        {"name": "Wheel Alignment", "number": "", "quantity": None, "amount": 1500.0, "priority": "Can Wait"},
    ]

    with patch.object(inventory, "_get_current_user") as auth_mock, \
         patch.object(inventory, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        bma.save_repair_priorities_batch("2026-11-28", "KDA 123A", items)

    assert auth_mock.call_count == 1
    assert db_ctx.call_count == 1
    cursor.execute.assert_called_once_with(
        "DELETE FROM tbl_repairpriorities WHERE RegNo = %s", ("KDA 123A",)
    )
    cursor.executemany.assert_called_once()
    inserted_rows = cursor.executemany.call_args.args[1]
    assert len(inserted_rows) == 2
    assert inserted_rows[0][2] == "Brake Pads"
    assert inserted_rows[1][4] is None

    with patch.object(inventory, "_get_current_user"):
        with pytest.raises(ValueError, match="Invalid registration"):
            bma.save_repair_priorities_batch("2026-11-28", "", items)
        with pytest.raises(ValueError, match="At least one"):
            bma.save_repair_priorities_batch("2026-11-28", "KDA 123A", [])

    with patch.object(inventory, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.save_repair_priorities_batch("2026-11-28", "KDA 123A", items)


def test_save_brand_comparison_batch_happy_invalid_and_unauth():
    cursor = MagicMock()
    items = [
        {"name": "Bosch Filter", "number": "BF-10", "quantity": 1, "amount": 1800.0, "groupid": "1"},
        {"name": "OEM Filter", "number": "OE-10", "quantity": 1, "amount": 0.0, "groupid": "1"},
    ]

    with patch.object(inventory, "_get_current_user") as auth_mock, \
         patch.object(inventory, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        bma.save_brand_comparison_batch("2026-11-28", "KDA 123A", items)

    assert auth_mock.call_count == 1
    assert db_ctx.call_count == 1
    cursor.execute.assert_called_once_with(
        "DELETE FROM tbl_brandcomparison WHERE RegNo = %s", ("KDA 123A",)
    )
    cursor.executemany.assert_called_once()
    inserted_rows = cursor.executemany.call_args.args[1]
    assert len(inserted_rows) == 2
    assert inserted_rows[0][6] == "1"

    with patch.object(inventory, "_get_current_user"):
        with pytest.raises(ValueError, match="Invalid registration"):
            bma.save_brand_comparison_batch("2026-11-28", None, items)
        with pytest.raises(ValueError, match="At least one"):
            bma.save_brand_comparison_batch("2026-11-28", "KDA 123A", [])

    with patch.object(inventory, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.save_brand_comparison_batch("2026-11-28", "KDA 123A", items)


def test_revision_caches_and_prewarms_all_four_subforms_for_zero_rebuild_switching(monkeypatch):
    class FakeButton:
        def __init__(self, text):
            self.text = text
            self.visible = False
            self.enabled = False
            self.background = "#0056D6"
            self.foreground = "white"

    iq_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="iq"))
    ai_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="ai"))
    rp_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="rp"))
    bc_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="bc"))

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
        "client_code.InterimQuotation": _module("client_code.InterimQuotation", InterimQuotation=iq_cls),
        "client_code.AmendedInvoice": _module("client_code.AmendedInvoice", AmendedInvoice=ai_cls),
        "client_code.RepairPriorities": _module("client_code.RepairPriorities", RepairPriorities=rp_cls),
        "client_code.BrandComparison": _module("client_code.BrandComparison", BrandComparison=bc_cls),
        "client_code.Revision._anvil_designer": _module(
            "client_code.Revision._anvil_designer",
            RevisionTemplate=type("RevisionTemplate", (), {}),
        ),
    }

    target = "client_code.Revision"
    monkeypatch.delitem(sys.modules, target, raising=False)
    for name, m in stubs.items():
        monkeypatch.setitem(sys.modules, name, m)

    mod = importlib.import_module(target)
    try:
        cls = mod.Revision
        b_iq = FakeButton("INTERIM QUOTATION")
        b_ai = FakeButton("AMENDED INVOICE")
        b_rp = FakeButton("REPAIR PRIORITIES")
        b_bc = FakeButton("BRAND COMPARISON")
        mounted = []

        form = SimpleNamespace(
            permissions={
                "REVISION": {
                    "main": True,
                    "subs": {
                        "Interim Quote": True,
                        "Amended Invoice": True,
                        "Repair Priorities": True,
                        "Brand Comparison": True,
                    },
                }
            },
            _initial_subform_loaded=False,
            _first_visible=None,
            _authorized_keys=[],
            _subforms={},
            _active_key=None,
            btn_InterimQuotation=b_iq,
            btn_AmendedInvoice=b_ai,
            btn_RepairPriorities=b_rp,
            btn_BrandComparison=b_bc,
            card_1=SimpleNamespace(get_components=lambda: [b_iq, b_ai, b_rp, b_bc]),
            card_2=SimpleNamespace(
                clear=lambda: mounted.clear(),
                add_component=lambda c: mounted.append(c),
                get_components=lambda: list(mounted),
            ),
        )
        form._build_subform = lambda k: cls._build_subform(form, k)
        form._get_or_create_subform = lambda k: cls._get_or_create_subform(form, k)
        form._prewarm_single_subform = lambda k: cls._prewarm_single_subform(form, k)
        form._schedule_prewarm_subforms = lambda: cls._schedule_prewarm_subforms(form)
        form._activate_subform = lambda k, b: cls._activate_subform(form, k, b)
        form.highlight_active_button = lambda t: cls.highlight_active_button(form, t)
        form.show_clicked_button = lambda n: cls.show_clicked_button(form, n)
        form.btn_InterimQuotation_click = lambda: cls.btn_InterimQuotation_click(form)
        form.btn_AmendedInvoice_click = lambda: cls.btn_AmendedInvoice_click(form)
        form.btn_RepairPriorities_click = lambda: cls.btn_RepairPriorities_click(form)
        form.btn_BrandComparison_click = lambda: cls.btn_BrandComparison_click(form)

        cls.apply_permissions(form)
        cls.form_show(form)

        # Drain idle pre-warm queue
        while timeouts:
            fn = timeouts.pop(0)
            fn()

        # All 4 subforms are now pre-built once in memory
        assert iq_cls.call_count == 1
        assert ai_cls.call_count == 1
        assert rp_cls.call_count == 1
        assert bc_cls.call_count == 1
        assert len(form._subforms) == 4

        # Clicking across all 4 tabs mounts cached instances with ZERO new instantiations!
        cls.btn_AmendedInvoice_click(form)
        assert mounted[-1].name == "ai"
        cls.btn_RepairPriorities_click(form)
        assert mounted[-1].name == "rp"
        cls.btn_BrandComparison_click(form)
        assert mounted[-1].name == "bc"
        cls.btn_InterimQuotation_click(form)
        assert mounted[-1].name == "iq"

        assert iq_cls.call_count == 1
        assert ai_cls.call_count == 1
        assert rp_cls.call_count == 1
        assert bc_cls.call_count == 1
    finally:
        sys.modules.pop(target, None)
