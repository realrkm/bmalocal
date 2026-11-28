import datetime
import importlib
import sys
import types
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import server_code.BMALocal as bma
from server_code import _common, invoices, orders, reports


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


@pytest.fixture(autouse=True)
def _clean_caches():
    _common.invalidate_lookup_cache()
    mod_cache = sys.modules.get("client_code.ModCache")
    if mod_cache is not None and hasattr(mod_cache, "clear"):
        mod_cache.clear()
    yield
    _common.invalidate_lookup_cache()
    mod_cache = sys.modules.get("client_code.ModCache")
    if mod_cache is not None and hasattr(mod_cache, "clear"):
        mod_cache.clear()


def test_get_reports_bootstrap_single_cursor_happy_invalid_and_unauth():
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        # 1. clients
        [(10, "Alice Doe", "0711000000", "Nairobi", "alice@example.com", "VIP")],
        # 2. car_details
        [("Alice Doe", "0711000000", "KDA 111A", "CH-001", datetime.date(2026, 11, 1), "JC-001", "BMW X5")],
        # 3. technicians_report
        [(3, "Bob Tech", "0722000000", "Box A", 0)],
        # 4. assigned_jobs
        [(datetime.date(2026, 11, 1), "JC-001", "Bob Tech", 15000.0, 3000.0, "BMW X5")],
        # 5. active_techs
        [(3, "Bob Tech")],
        # 6. staffs_report
        [(5, "Carol Staff", "0733000000", 0)],
        # 7. price_catalogue
        [("Oil Filter", "OF-01", 5, 800.0, 1500.0, 100.0, datetime.date(2026, 10, 15), 12)],
        # 8. stock_location
        [(1, "Oil Filter", "OF-01", "Shelf A")],
        # 9. stock_balance
        [(1, "Oil Filter", "OF-01", 5, 3, 0, datetime.date(2026, 10, 15), 15, 12, "No")],
        # 10. quote_invoice_totals
        [(101, datetime.date(2026, 11, 1), "JC-001", 16000.0, 15000.0)],
        # 11. payment_summary
        [("Alice Doe", "0711000000", "JC-001", datetime.date(2026, 11, 1), 10000.0, 500.0, 4500.0)],
    ]

    with patch.object(reports, "_get_current_user", return_value={"role_id": 1}), \
         patch.object(reports, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        bundle = bma.get_reports_bootstrap()

    # Single DB connection checkout for all 7 sections!
    assert db_ctx.call_count == 1
    assert bundle["clients"][0]["Fullname"] == "Alice Doe"
    assert bundle["car_details"][0]["RegNo"] == "KDA 111A"
    assert bundle["technicians_report"][0]["Toolkit"] == "Box A"
    assert bundle["assigned_jobcards"]["jobs"][0]["InvoicedAmount"] == "15,000.00"
    assert bundle["assigned_jobcards"]["technicians"] == [("Bob Tech", 3)]
    assert bundle["staffs_report"][0]["Fullname"] == "Carol Staff"
    assert bundle["price_catalogue"][0]["Selling"] == "1,500.00"
    assert bundle["stock_location"][0]["Location"] == "Shelf A"
    assert bundle["stock_balance"][0]["StockBalance"] == "12.00"
    assert bundle["quote_invoice_totals"][0]["InvoiceTotal"] == "15,000.00"
    assert bundle["payment_summary"][0]["Balance"] == "4,500.00"

    # Empty section list returns {} with 0 DB checkouts
    with patch.object(reports, "_get_current_user", return_value={"role_id": 1}), \
         patch.object(reports, "db_cursor") as db_ctx_empty:
        assert bma.get_reports_bootstrap([]) == {}
        assert db_ctx_empty.call_count == 0

    # Invalid inputs rejected
    with patch.object(reports, "_get_current_user", return_value={"role_id": 1}):
        with pytest.raises(ValueError, match="sections must be a list"):
            bma.get_reports_bootstrap("clients")
        with pytest.raises(ValueError, match="Invalid report bootstrap section"):
            bma.get_reports_bootstrap(["clients", "bogus"])

    # Unauthenticated caller rejected
    with patch.object(reports, "_get_current_user", side_effect=PermissionError("Authentication required")):
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.get_reports_bootstrap()


def test_monthly_schedule_bundle_and_batch_save_happy_invalid_unauth():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        (datetime.date(2026, 11, 2), "Brake Pads", "BP-01", 2, 4500.0),
    ]
    cursor.fetchone.side_effect = [
        ("Alice Doe", 9000.0),
        (5000.0, 500.0),
    ]

    d1 = datetime.date(2026, 11, 1)
    d2 = datetime.date(2026, 11, 30)
    with patch.object(orders, "_get_current_user", return_value={"role_id": 1}), \
         patch.object(orders, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        res = bma.get_periodic_invoices_with_summary(d1, d2, 42)

    assert db_ctx.call_count == 1
    assert res["invoices"][0]["Item"] == "Brake Pads"
    assert res["invoices"][0]["Amount"] == "4,500.00"
    assert res["summary"] == {
        "Fullname": "Alice Doe",
        "TotalInvoiceAmount": 9000.0,
        "TotalAmountPaid": 5000.0,
        "TotalDiscount": 500.0,
        "Balance": 3500.0,
    }

    with patch.object(orders, "_get_current_user", return_value={"role_id": 1}):
        with pytest.raises(ValueError, match="Invalid jobcard_id"):
            bma.get_periodic_invoices_with_summary(d1, d2, 0)
        with pytest.raises(ValueError, match="start_date cannot be greater"):
            bma.get_periodic_invoices_with_summary(d2, d1, 42)

    with patch.object(orders, "_get_current_user", side_effect=PermissionError("Authentication required")):
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.get_periodic_invoices_with_summary(d1, d2, 42)

    # Batch save replaces N+1 inserts with 1 DELETE + 1 executemany
    save_cursor = MagicMock()
    rows = [
        {"Date": "2026-11-02", "Item": "Brake Pads", "Part_No": "BP-01", "QuantityIssued": 2, "Amount": "4,500.00", "Category": "Car Parts"},
        {"Date": "2026-11-02", "Item": "Labour", "Part_No": "", "QuantityIssued": None, "Amount": "2,000.00", "Category": "Labour"},
    ]
    with patch.object(orders, "_get_current_user", return_value={"role_id": 1}), \
         patch.object(orders, "publish_realtime_event") as pub_mock, \
         patch.object(orders, "db_cursor") as save_ctx:
        save_ctx.return_value.__enter__.return_value = save_cursor
        out = bma.save_monthly_schedule_batch(42, "Alice Doe", 11000, 5000, 500, 5500, rows)

    assert out == {"success": True, "saved_count": 2}
    save_cursor.execute.assert_called_once_with(
        "DELETE FROM tbl_monthlyschedule WHERE AssignedJobID = %s",
        (42,),
    )
    save_cursor.executemany.assert_called_once()
    assert len(save_cursor.executemany.call_args.args[1]) == 2
    pub_mock.assert_called_once_with("payments", "monthly_schedule_saved", entity_id=42)

    with patch.object(orders, "_get_current_user", return_value={"role_id": 1}):
        with pytest.raises(ValueError, match="Invalid jobcard_id"):
            bma.save_monthly_schedule_batch(None, "Alice", 0, 0, 0, 0, rows)
        with pytest.raises(ValueError, match="non-empty list"):
            bma.save_monthly_schedule_batch(42, "Alice", 0, 0, 0, 0, [])
        with pytest.raises(ValueError, match="Missing category"):
            bma.save_monthly_schedule_batch(42, "Alice", 0, 0, 0, 0, [{"Item": "Oil", "Category": "  "}])

    with patch.object(orders, "_get_current_user", side_effect=PermissionError("Authentication required")):
        with pytest.raises(PermissionError, match="Authentication required"):
            bma.save_monthly_schedule_batch(42, "Alice", 0, 0, 0, 0, rows)


def test_get_client_payment_summary_eliminates_correlated_subquery():
    cursor = MagicMock()
    cursor.description = [
        ("Fullname",),
        ("Phone",),
        ("JobCardRef",),
        ("ReceivedDate",),
        ("TotalPaid",),
        ("Discount",),
        ("LatestBalance",),
    ]
    cursor.fetchall.return_value = [
        ("Alice Doe", "0711000000", "JC-001", datetime.date(2026, 11, 5), 8000.0, 500.0, 1500.0),
    ]
    with patch.object(invoices, "_get_current_user", return_value={"role_id": 1}), \
         patch.object(invoices, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        rows = bma.get_client_payment_summary()

    executed_sql = cursor.execute.call_args.args[0]
    assert "ORDER BY tbl_payments.ID DESC" not in executed_sql
    assert "LEFT JOIN" in executed_sql
    assert rows == [
        {
            "No": 1,
            "JobReceivedDate": "2026-11-05",
            "JobCardRef": "JC-001",
            "Fullname": "Alice Doe",
            "Phone": "0711000000",
            "TotalPaid": "8,000.00",
            "Discount": "500.00",
            "Balance": "1,500.00",
        }
    ]


def test_report_hub_prewarms_and_switches_all_9_reports_with_zero_rebuilds(monkeypatch):
    timeouts = []
    warm_calls = []

    def _make_stub_report(label):
        def _factory(*args, **kwargs):
            filters = [args[0] if args else None]
            return SimpleNamespace(
                label=label,
                filters=filters,
                set_filter=lambda val: filters.append(val),
            )
        return MagicMock(side_effect=_factory)

    report_factories = {
        "ClientContactReport": _make_stub_report("Clients"),
        "CarDetailsReport": _make_stub_report("Car Details"),
        "TechnicianJobCardDetails": _make_stub_report("Technicians"),
        "StaffDetailsReport": _make_stub_report("Staffs"),
        "InventoryReport": _make_stub_report("Inventory"),
        "PeriodicQuoteVsInvoice": _make_stub_report("Periodic Quote And Invoice"),
        "PeriodicPayment": _make_stub_report("Periodic Payment Details"),
        "MonthlyPerformanceSchedule": _make_stub_report("Monthly Performance Schedule"),
        "ServiceHistory": _make_stub_report("Service History"),
    }

    anvil = _module("anvil", Notification=MagicMock())
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=MagicMock(), call_s=MagicMock(), no_loading_indicator=nullcontext())
    anvil_js = _module(
        "anvil.js",
        call=MagicMock(),
        get_dom_node=MagicMock(return_value=SimpleNamespace(addEventListener=MagicMock())),
        window=SimpleNamespace(setTimeout=lambda fn, _ms=0: timeouts.append(fn), bmaRealtime=None),
    )
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.js = anvil_js

    class FakeReportTemplate:
        def init_components(self, **_kw):
            self.card_panel = SimpleNamespace(
                components=[],
                visible=False,
                clear=lambda: self.card_panel.components.clear(),
                add_component=lambda c, **_k: self.card_panel.components.append(c),
            )
            self.cmbReport = SimpleNamespace(items=[], selected_value=None, focus=lambda: None)
            self.search_keyword_1 = SimpleNamespace(
                text_box_search=SimpleNamespace(visible=False, text="", placeholder="", focus=lambda: None),
                repeating_panel_results=SimpleNamespace(visible=False),
                selected_result=None,
                set_event_handler=lambda *_a, **_k: None,
            )

        def set_event_handler(self, *_a, **_kw):
            pass

    mod_get_data = _module(
        "client_code.ModGetData",
        warmReportsCaches=lambda perms=None: warm_calls.append(perms),
        getClientFullnameCached=lambda: [{"ID": 7, "Fullname": "Alice Doe"}],
        getTechniciansCached=lambda: [{"ID": 3, "Fullname": "Bob Tech"}],
        getStaffCached=lambda: [{"ID": 5, "Staff": "Carol Staff"}],
    )

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.js": anvil_js,
        "client_code.ModGetData": mod_get_data,
        "client_code.Report._anvil_designer": _module(
            "client_code.Report._anvil_designer",
            ReportTemplate=FakeReportTemplate,
        ),
    }
    for cls_name, factory in report_factories.items():
        stubs[f"client_code.{cls_name}"] = _module(f"client_code.{cls_name}", **{cls_name: factory})

    monkeypatch.delitem(sys.modules, "client_code.Report", raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)
    import client_code
    monkeypatch.setattr(client_code, "ModGetData", mod_get_data, raising=False)

    report_mod = importlib.import_module("client_code.Report")
    try:
        perms = {
            "REPORTS": {
                "main": True,
                "subs": {
                    "Client Report": True,
                    "Car Details Report": True,
                    "Technicians Report": True,
                    "Staffs Report": True,
                    "Inventory Report": True,
                    "Quote And Invoice Report": True,
                    "Payment Report": True,
                    "Monthly Schedule": True,
                    "Service History": True,
                },
            }
        }
        form = report_mod.Report(perms)
        assert len(form.cmbReport.items) == 9
        assert form.cmbReport.items == sorted(form.cmbReport.items)

        # Trigger form_show and flush 0ms idle pre-warm slices
        form.form_show()
        while timeouts:
            timeouts.pop(0)()

        assert len(warm_calls) == 1
        for factory in report_factories.values():
            assert factory.call_count == 1

        # Cycle through all 9 cmbReport options twice -> ZERO additional instantiations!
        all_labels = list(form.cmbReport.items)
        for _round in range(2):
            for label in all_labels:
                form.cmbReport.selected_value = label
                form.cmbReport_change()
                assert form.card_panel.visible is True
                assert form.card_panel.components[-1].label == label

        for factory in report_factories.values():
            assert factory.call_count == 1

        # Filtering Clients via searchValue updates in place via set_filter without reconstructing
        form.cmbReport.selected_value = "Clients"
        form.search_keyword_1.selected_result = {"ID": 7}
        form.searchValue({"ID": 7})
        assert report_factories["ClientContactReport"].call_count == 1
        assert form._subforms["Clients"].filters[-1] == 7

        # Re-selecting Clients in cmbReport resets filter to None in place
        form.cmbReport_change()
        assert form._subforms["Clients"].filters[-1] is None
        assert report_factories["ClientContactReport"].call_count == 1

        # Cached getValue("Clients") makes 0 blocking anvil.server.call round-trips
        assert form.getValue() == [{"entry": "Alice Doe", "ID": 7}]
        assert anvil_server.call.call_count == 0
    finally:
        sys.modules.pop("client_code.Report", None)


def test_inventory_report_and_technician_subhubs_prewarm_and_cache_tabs(monkeypatch):
    class FakeButton:
        def __init__(self, text):
            self.text = text
            self.background = "#0056D6"
            self.foreground = "white"

    timeouts = []
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

    inv_factories = {
        "PriceCatalogue": MagicMock(side_effect=lambda: SimpleNamespace(tab="cat")),
        "StockLocation": MagicMock(side_effect=lambda: SimpleNamespace(tab="loc")),
        "StockBalance": MagicMock(side_effect=lambda: SimpleNamespace(tab="bal")),
        "StocktakeAnalysis": MagicMock(side_effect=lambda: SimpleNamespace(tab="ana")),
        "CarPartsUsed": MagicMock(side_effect=lambda: SimpleNamespace(tab="used")),
    }
    tech_factories = {
        "TechniciansDetailsReport": MagicMock(side_effect=lambda: SimpleNamespace(tab="tech")),
        "AssignedJobCards": MagicMock(side_effect=lambda: SimpleNamespace(tab="jobs")),
    }

    class FakeInvTemplate:
        def init_components(self, **_kw):
            self.btn_PriceCatalogue = FakeButton("PRICE CATALOGUE")
            self.btn_Location = FakeButton("STOCK LOCATION")
            self.btn_StockBalance = FakeButton("STOCK BALANCE")
            self.btn_StocktakeAnalysis = FakeButton("STOCK ANALYSIS")
            self.btn_CarPartsUsed = FakeButton("CAR PARTS USED")
            btns = [
                self.btn_PriceCatalogue,
                self.btn_Location,
                self.btn_StockBalance,
                self.btn_StocktakeAnalysis,
                self.btn_CarPartsUsed,
            ]
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

    class FakeTechTemplate:
        def init_components(self, **_kw):
            self.btn_Technician = FakeButton("TECHNICIANS")
            self.btn_AssignedJobCards = FakeButton("ASSIGNED JOB CARDS")
            btns = [self.btn_Technician, self.btn_AssignedJobCards]
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

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "anvil.js": anvil_js,
        "client_code.InventoryReport._anvil_designer": _module(
            "client_code.InventoryReport._anvil_designer",
            InventoryReportTemplate=FakeInvTemplate,
        ),
        "client_code.TechnicianJobCardDetails._anvil_designer": _module(
            "client_code.TechnicianJobCardDetails._anvil_designer",
            TechnicianJobCardDetailsTemplate=FakeTechTemplate,
        ),
    }
    for name, factory in {**inv_factories, **tech_factories}.items():
        stubs[f"client_code.{name}"] = _module(f"client_code.{name}", **{name: factory})

    monkeypatch.delitem(sys.modules, "client_code.InventoryReport", raising=False)
    monkeypatch.delitem(sys.modules, "client_code.TechnicianJobCardDetails", raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)

    inv_mod = importlib.import_module("client_code.InventoryReport")
    tech_mod = importlib.import_module("client_code.TechnicianJobCardDetails")
    try:
        inv_form = inv_mod.InventoryReport("Catalogue")
        inv_form.form_show()
        while timeouts:
            timeouts.pop(0)()

        for factory in inv_factories.values():
            assert factory.call_count == 1

        inv_form.btn_Location_click()
        inv_form.btn_StockBalance_click()
        inv_form.btn_StocktakeAnalysis_click()
        inv_form.btn_CarPartsUsed_click()
        inv_form.btn_PriceCatalogue_click()
        for factory in inv_factories.values():
            assert factory.call_count == 1

        tech_form = tech_mod.TechnicianJobCardDetails()
        tech_form.form_show()
        while timeouts:
            timeouts.pop(0)()

        for factory in tech_factories.values():
            assert factory.call_count == 1

        tech_form.btn_AssignedJobCards_click()
        tech_form.btn_Technician_click()
        for factory in tech_factories.values():
            assert factory.call_count == 1
    finally:
        sys.modules.pop("client_code.InventoryReport", None)
        sys.modules.pop("client_code.TechnicianJobCardDetails", None)


def test_warm_cache_subforms_mount_immediately_with_zero_rpcs(monkeypatch):
    timeouts = []
    server_call = MagicMock()
    anvil = _module("anvil", Notification=MagicMock(), alert=MagicMock())
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=server_call, call_s=server_call, no_loading_indicator=nullcontext())
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

    cached_clients = [
        {"No": 1, "ID": 10, "Fullname": "Alice Doe"},
        {"No": 2, "ID": 20, "Fullname": "Bob Roe"},
    ]
    cached_catalogue = [{"No": 1, "Name": "Oil Filter", "PartNo": "OF-1"}]
    cached_assigned = {
        "jobs": [{"No": 1, "InvoicedAmount": "12,000.00", "LabourAmount": "2,500.00"}],
        "technicians": [("Bob Tech", 3)],
    }

    mod_get_data = _module(
        "client_code.ModGetData",
        peekClientReportCached=lambda: cached_clients,
        getClientReportCached=lambda force_refresh=False: cached_clients,
        peekPriceCatalogueCached=lambda: cached_catalogue,
        getPriceCatalogueCached=lambda force_refresh=False: cached_catalogue,
        peekAssignedJobcardsBootstrapCached=lambda: cached_assigned,
        getAssignedJobcardsBootstrapCached=lambda force_refresh=False: cached_assigned,
    )

    class FakeCCRTemplate:
        def init_components(self, **_kw):
            self.data_grid_1 = SimpleNamespace(show_page_controls=False)
            self.client_repeater = SimpleNamespace(items=[])

        def set_event_handler(self, *_a, **_kw):
            pass

    class FakePCTemplate:
        def init_components(self, **_kw):
            self.data_grid_1 = SimpleNamespace(show_page_controls=False, role=None)
            self.repeating_panel_1 = SimpleNamespace(items=[])
            self.text_box_search = SimpleNamespace(text="")

        def set_event_handler(self, *_a, **_kw):
            pass

    class FakeAJCTemplate:
        def init_components(self, **_kw):
            self.repeating_panel_1 = SimpleNamespace(items=[])
            self.drop_down_selectTechnician = SimpleNamespace(items=[], selected_value=None)
            self.labelInvoiceTotal = SimpleNamespace(text="")
            self.labelLabourTotal = SimpleNamespace(text="")
            self.date_picker_start = SimpleNamespace(date=None)
            self.date_picker_end = SimpleNamespace(date=None)

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
        "client_code.ClientContactReport._anvil_designer": _module(
            "client_code.ClientContactReport._anvil_designer",
            ClientContactReportTemplate=FakeCCRTemplate,
        ),
        "client_code.PriceCatalogue._anvil_designer": _module(
            "client_code.PriceCatalogue._anvil_designer",
            PriceCatalogueTemplate=FakePCTemplate,
        ),
        "client_code.AssignedJobCards._anvil_designer": _module(
            "client_code.AssignedJobCards._anvil_designer",
            AssignedJobCardsTemplate=FakeAJCTemplate,
        ),
    }

    for mod_name in ("client_code.ClientContactReport", "client_code.PriceCatalogue", "client_code.AssignedJobCards"):
        monkeypatch.delitem(sys.modules, mod_name, raising=False)
    for name, mod in stubs.items():
        monkeypatch.setitem(sys.modules, name, mod)
    import client_code
    monkeypatch.setattr(client_code, "ModGetData", mod_get_data, raising=False)

    ccr_mod = importlib.import_module("client_code.ClientContactReport")
    pc_mod = importlib.import_module("client_code.PriceCatalogue")
    ajc_mod = importlib.import_module("client_code.AssignedJobCards")
    try:
        ccr = ccr_mod.ClientContactReport(None)
        pc = pc_mod.PriceCatalogue()
        ajc = ajc_mod.AssignedJobCards()

        # Populated immediately in 0ms with ZERO server calls and ZERO deferred setTimeouts!
        assert server_call.call_count == 0
        assert timeouts == []
        assert ccr.client_repeater.items == cached_clients
        assert pc.repeating_panel_1.items == cached_catalogue
        assert ajc.labelInvoiceTotal.text == "12,000.00"
        assert ajc.labelLabourTotal.text == "2,500.00"

        # Filtering ClientContactReport in-place uses RAM cache with 0 RPCs
        ccr.set_filter(20)
        assert ccr.client_repeater.items == [{"No": 1, "ID": 20, "Fullname": "Bob Roe"}]
        ccr.set_filter(None)
        assert ccr.client_repeater.items == cached_clients
        assert server_call.call_count == 0
    finally:
        for mod_name in ("client_code.ClientContactReport", "client_code.PriceCatalogue", "client_code.AssignedJobCards"):
            sys.modules.pop(mod_name, None)
