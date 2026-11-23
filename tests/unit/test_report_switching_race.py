import importlib
import sys
import types


def _load_report_form(monkeypatch, slow_factory):
    """Load client_code.Report with stubbed Anvil components to simulate out-of-order report instantiation."""
    fake_anvil = types.ModuleType("anvil")
    fake_anvil.Notification = lambda *a, **kw: types.SimpleNamespace(show=lambda: None)
    fake_anvil.Label = lambda **kw: types.SimpleNamespace(**kw)
    fake_anvil.tables = types.ModuleType("anvil.tables")
    fake_anvil.tables.query = types.ModuleType("anvil.tables.query")
    fake_anvil.tables.app_tables = types.SimpleNamespace()
    fake_anvil.server = types.ModuleType("anvil.server")
    fake_anvil.server.call = lambda *a, **kw: []
    fake_anvil.js = types.ModuleType("anvil.js")
    fake_anvil.js.call = lambda *a, **kw: None
    fake_anvil.js.window = types.SimpleNamespace(setTimeout=lambda fn, ms: fn())

    monkeypatch.setitem(sys.modules, "anvil", fake_anvil)
    monkeypatch.setitem(sys.modules, "anvil.tables", fake_anvil.tables)
    monkeypatch.setitem(sys.modules, "anvil.tables.query", fake_anvil.tables.query)
    monkeypatch.setitem(sys.modules, "anvil.server", fake_anvil.server)
    monkeypatch.setitem(sys.modules, "anvil.js", fake_anvil.js)

    # Stub template and child report modules
    fake_designer = types.ModuleType("client_code.Report._anvil_designer")

    class FakeCardPanel:
        def __init__(self):
            self.components = []
            self.visible = False

        def clear(self):
            self.components.clear()

        def add_component(self, comp, **kw):
            self.components.append(comp)

    class FakeSearchKeyword:
        def __init__(self):
            self.text_box_search = types.SimpleNamespace(visible=False, text="", placeholder="", focus=lambda: None)
            self.repeating_panel_results = types.SimpleNamespace(visible=False)
            self.selected_result = None

        def set_event_handler(self, *a, **kw):
            pass

    class FakeDropDown:
        def __init__(self):
            self.items = []
            self.selected_value = None

        def focus(self):
            pass

    class ReportTemplate:
        def init_components(self, **kw):
            self.card_panel = FakeCardPanel()
            self.cmbReport = FakeDropDown()
            self.search_keyword_1 = FakeSearchKeyword()

        def set_event_handler(self, *a, **kw):
            pass

    fake_designer.ReportTemplate = ReportTemplate
    monkeypatch.setitem(sys.modules, "client_code.Report._anvil_designer", fake_designer)

    fake_mod_get_data = types.ModuleType("client_code.ModGetData")
    monkeypatch.setitem(sys.modules, "client_code.ModGetData", fake_mod_get_data)

    # Stub ClientContactReport & CarDetailsReport
    ccr_mod = types.ModuleType("client_code.ClientContactReport")
    ccr_mod.ClientContactReport = lambda client_id: {"form": "ClientContactReport", "client_id": client_id}
    monkeypatch.setitem(sys.modules, "client_code.ClientContactReport", ccr_mod)

    cdr_mod = types.ModuleType("client_code.CarDetailsReport")
    cdr_mod.CarDetailsReport = slow_factory
    monkeypatch.setitem(sys.modules, "client_code.CarDetailsReport", cdr_mod)

    if "client_code.Report" in sys.modules:
        del sys.modules["client_code.Report"]
    report_mod = importlib.import_module("client_code.Report")
    return report_mod


def test_rapid_report_switching_does_not_display_stale_car_details_over_clients(monkeypatch):
    """
    Reproduce: User selects Clients -> Car Details (slow) -> Clients (fast).
    While CarDetailsReport.__init__ is suspended awaiting the server, the user switches
    cmbReport back to Clients, which finishes and renders Clients. When CarDetailsReport
    finally returns, it MUST NOT overwrite Clients in card_panel.
    """
    form_holder = {}

    def slow_car_details_factory():
        # Simulate user switching cmbReport back to "Clients" while Car Details is still loading!
        report_form = form_holder["form"]
        report_form.cmbReport.selected_value = "Clients"
        report_form.cmbReport_change()
        # Now Car Details finishes loading AFTER Clients already rendered
        return {"form": "CarDetailsReport"}

    report_mod = _load_report_form(monkeypatch, slow_car_details_factory)
    report_form = report_mod.Report(permissions={"REPORTS": {"main": True, "subs": {}}})
    form_holder["form"] = report_form

    # 1. Select Clients
    report_form.cmbReport.selected_value = "Clients"
    report_form.cmbReport_change()

    # 2. Switch to Car Details (which internally simulates switching back to Clients mid-flight)
    report_form.cmbReport.selected_value = "Car Details"
    report_form.cmbReport_change()

    # Final state: cmbReport is "Clients", so card_panel MUST display ONLY ClientContactReport
    assert report_form.cmbReport.selected_value == "Clients"
    assert report_form.card_panel.components == [{"form": "ClientContactReport", "client_id": None}]


def test_client_contact_report_loads_data_after_form_show(monkeypatch):
    """
    Regression test: form_show fires immediately when ClientContactReport is mounted,
    BEFORE the 10ms setTimeout(_load_initial_data) fires. form_show must NOT clear
    _is_mounted and silently skip loading client details into client_repeater.
    """
    scheduled_callbacks = []

    class _NoSpinner:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    fake_anvil = types.ModuleType("anvil")
    fake_anvil.FlowPanel = lambda **kw: types.SimpleNamespace(add_component=lambda *a, **k: None, visible=True)
    fake_anvil.Button = lambda **kw: types.SimpleNamespace(set_event_handler=lambda *a, **k: None, enabled=False)
    fake_anvil.Label = lambda **kw: types.SimpleNamespace(**kw)
    fake_anvil.tables = types.ModuleType("anvil.tables")
    fake_anvil.tables.query = types.ModuleType("anvil.tables.query")
    fake_anvil.tables.app_tables = types.SimpleNamespace()
    fake_anvil.users = types.ModuleType("anvil.users")
    fake_anvil.server = types.ModuleType("anvil.server")
    fake_anvil.server.no_loading_indicator = _NoSpinner()
    fake_anvil.server.call = lambda fn, *a, **kw: [
        {"No": 1, "ID": 10, "Fullname": "Jane Doe"}
    ]
    fake_anvil.js = types.ModuleType("anvil.js")
    fake_anvil.js.call = lambda *a, **kw: None
    fake_anvil.js.window = types.SimpleNamespace(
        setTimeout=lambda fn, ms: scheduled_callbacks.append(fn),
        bmaRealtime=None,
    )

    monkeypatch.setitem(sys.modules, "anvil", fake_anvil)
    monkeypatch.setitem(sys.modules, "anvil.tables", fake_anvil.tables)
    monkeypatch.setitem(sys.modules, "anvil.tables.query", fake_anvil.tables.query)
    monkeypatch.setitem(sys.modules, "anvil.users", fake_anvil.users)
    monkeypatch.setitem(sys.modules, "anvil.server", fake_anvil.server)
    monkeypatch.setitem(sys.modules, "anvil.js", fake_anvil.js)

    fake_designer = types.ModuleType("client_code.ClientContactReport._anvil_designer")

    class ClientContactReportTemplate:
        def init_components(self, **kw):
            self.data_grid_1 = types.SimpleNamespace(rows_per_page=25, show_page_controls=True)
            self.client_repeater = types.SimpleNamespace(items=[])
            self._handlers = {}

        def add_component(self, comp, **kw):
            pass

        def set_event_handler(self, ev, fn):
            self._handlers[ev] = fn

    fake_designer.ClientContactReportTemplate = ClientContactReportTemplate
    monkeypatch.setitem(sys.modules, "client_code.ClientContactReport._anvil_designer", fake_designer)

    sys.modules.pop("client_code.ClientContactReport", None)

    ccr_mod = importlib.import_module("client_code.ClientContactReport")
    form = ccr_mod.ClientContactReport(None)

    # Anvil fires 'show' right when the component is added to card_panel
    form.form_show()
    # 10ms later the scheduled initial data load runs
    assert len(scheduled_callbacks) == 1
    scheduled_callbacks[0]()

    assert form.client_repeater.items == [{"No": 1, "ID": 10, "Fullname": "Jane Doe"}]
