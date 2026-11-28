from ._anvil_designer import ReportTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.js
from .. import ModGetData

class Report(ReportTemplate):
    def __init__(self, permissions, **properties):
        self.init_components(**properties)

        anvil.js.call('replaceBanner')
        self.card_panel.visible = False

        self.cmbReport.focus()

        # Attach the event that fetches searched values
        self.search_keyword_1.set_event_handler('x-get-search-keys', self.getValue)

        # Handle what happens when a user selects a result
        self.search_keyword_1.set_event_handler('x-search-hints-result', self.searchValue)

        self.permissions = permissions
        self._report_load_seq = 0
        self._subforms = {}
        self._authorized_reports = []
        self._prewarm_started = False

        # Apply permissions to dropdown in a single sorted pass
        self.apply_permissions()
        self._attach_dropdown_prewarm()
        self.set_event_handler("show", self.form_show)

    def apply_permissions(self):
        """Apply only REPORT-related permissions in a single sorted pass."""
        report_perms = (self.permissions or {}).get("REPORTS", {"main": False, "subs": {}})
        subs = report_perms.get("subs", {})
        perm_map = (
            ("Client Report", "Clients"),
            ("Car Details Report", "Car Details"),
            ("Technicians Report", "Technicians"),
            ("Staffs Report", "Staffs"),
            ("Inventory Report", "Inventory"),
            ("Quote And Invoice Report", "Periodic Quote And Invoice"),
            ("Payment Report", "Periodic Payment Details"),
            ("Monthly Schedule", "Monthly Performance Schedule"),
            ("Service History", "Service History"),
        )
        items = sorted(label for perm_key, label in perm_map if subs.get(perm_key))
        self.cmbReport.items = items
        self._authorized_reports = list(items)

    def add_item(self, new_item):
        items = list(self.cmbReport.items or [])
        items.append(new_item)
        items.sort()
        self.cmbReport.items = items

    def _build_subform(self, report_name):
        if report_name == "Clients":
            from ..ClientContactReport import ClientContactReport
            return ClientContactReport(None)
        if report_name == "Car Details":
            from ..CarDetailsReport import CarDetailsReport
            return CarDetailsReport()
        if report_name == "Technicians":
            from ..TechnicianJobCardDetails import TechnicianJobCardDetails
            return TechnicianJobCardDetails("Technician")
        if report_name == "Staffs":
            from ..StaffDetailsReport import StaffDetailsReport
            return StaffDetailsReport(None)
        if report_name == "Inventory":
            from ..InventoryReport import InventoryReport
            return InventoryReport("Catalogue")
        if report_name == "Periodic Quote And Invoice":
            from ..PeriodicQuoteVsInvoice import PeriodicQuoteVsInvoice
            return PeriodicQuoteVsInvoice()
        if report_name == "Periodic Payment Details":
            from ..PeriodicPayment import PeriodicPayment
            return PeriodicPayment()
        if report_name == "Monthly Performance Schedule":
            from ..MonthlyPerformanceSchedule import MonthlyPerformanceSchedule
            return MonthlyPerformanceSchedule()
        if report_name == "Service History":
            from ..ServiceHistory import ServiceHistory
            return ServiceHistory()
        return None

    def _get_or_create_subform(self, report_name):
        subforms = getattr(self, "_subforms", None)
        if subforms is None:
            self._subforms = subforms = {}
        inst = subforms.get(report_name)
        if inst is None:
            inst = self._build_subform(report_name)
            if inst is not None:
                subforms[report_name] = inst
        return inst

    def _prewarm_single_subform(self, report_name):
        subforms = getattr(self, "_subforms", None)
        if subforms is not None and report_name in subforms:
            return
        try:
            self._get_or_create_subform(report_name)
        except Exception:
            pass

    def _trigger_background_warm(self, _evt=None):
        if getattr(self, "_prewarm_started", False):
            return
        self._prewarm_started = True
        reports = list(getattr(self, "_authorized_reports", ()))

        def _warm_data_then_forms():
            try:
                warm_fn = getattr(ModGetData, "warmReportsCaches", None)
                if callable(warm_fn):
                    warm_fn(self.permissions)
            except Exception:
                pass

            def _step(idx=0):
                if idx >= len(reports):
                    return
                self._prewarm_single_subform(reports[idx])
                try:
                    anvil.js.window.setTimeout(lambda: _step(idx + 1), 0)
                except Exception:
                    pass

            if reports:
                try:
                    anvil.js.window.setTimeout(lambda: _step(0), 0)
                except Exception:
                    pass

        try:
            anvil.js.window.setTimeout(_warm_data_then_forms, 0)
        except Exception:
            pass

    def _attach_dropdown_prewarm(self):
        get_dom = getattr(anvil.js, "get_dom_node", None)
        if not callable(get_dom):
            return
        try:
            dom_node = get_dom(self.cmbReport)
            dom_node.addEventListener("pointerenter", self._trigger_background_warm, {"passive": True})
            dom_node.addEventListener("mousedown", self._trigger_background_warm, {"passive": True})
            dom_node.addEventListener("touchstart", self._trigger_background_warm, {"passive": True})
            dom_node.addEventListener("focus", self._trigger_background_warm, {"passive": True})
        except Exception:
            pass

    def form_show(self, **event_args):
        """Warm report caches and pre-build authorized report subforms once Report opens."""
        self._trigger_background_warm()

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def _mount_report(self, load_seq, expected_report, component):
        """Mount a report component only if it still matches the latest combobox selection."""
        if load_seq != self._report_load_seq or self.cmbReport.selected_value != expected_report:
            return
        self.card_panel.clear()
        if component is not None:
            self.card_panel.add_component(component, full_width_row=True)
            self.card_panel.visible = True
        else:
            self.card_panel.visible = False

    def _configure_search_bar(self, selected):
        if selected == "Clients":
            self.search_keyword_1.text_box_search.visible = True
            self.search_keyword_1.repeating_panel_results.visible = True
            self.search_keyword_1.text_box_search.text = ""
            self.search_keyword_1.text_box_search.placeholder = "Search Client's Name"
            self.search_keyword_1.text_box_search.focus()
        elif selected == "Staffs":
            self.search_keyword_1.text_box_search.visible = True
            self.search_keyword_1.repeating_panel_results.visible = True
            self.search_keyword_1.text_box_search.text = ""
            self.search_keyword_1.text_box_search.placeholder = "Search Staff's Name"
            self.search_keyword_1.text_box_search.focus()
        else:
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False

    def cmbReport_change(self, **event_args):
        """Mount cached/pre-warmed report subform in milliseconds when selected."""
        selected = self.cmbReport.selected_value
        self._report_load_seq += 1
        load_seq = self._report_load_seq

        if not selected:
            self.card_panel.clear()
            self.card_panel.visible = False
            return

        self._configure_search_bar(selected)
        comp = self._get_or_create_subform(selected)
        if selected in ("Clients", "Staffs") and hasattr(comp, "set_filter"):
            comp.set_filter(None)
        self._mount_report(load_seq, selected, comp)

    def getValue(self, **event_args):
        """Return cached autocomplete search items for Clients, Technicians, or Staffs."""
        selectedReport = self.cmbReport.selected_value

        if selectedReport == "Clients":
            cached_fn = getattr(ModGetData, "getClientFullnameCached", None)
            results = cached_fn() if callable(cached_fn) else anvil.server.call("getClientFullname")
            return [{'entry': r['Fullname'], 'ID': r['ID']} for r in (results or [])]

        elif selectedReport == "Technicians":
            results = ModGetData.getTechniciansCached()
            return [{'entry': r['Fullname'], 'ID': r['ID']} for r in (results or [])]

        elif selectedReport == "Staffs":
            results = ModGetData.getStaffCached()
            return [{'entry': r['Staff'], 'ID': r['ID']} for r in (results or [])]

    def searchValue(self, result, **event_args):
        """Filter the active report in place when a search hint is selected."""
        selected_id = result['ID']
        selected = self.cmbReport.selected_value
        self._report_load_seq += 1
        load_seq = self._report_load_seq

        if selected == "Clients":
            if selected_id is None:
                Notification("Client is not found. Enter correct name of the client", title="Missing Client Details", style="danger", timeout=3).show()
                self.card_panel.clear()
                self.card_panel.visible = False
            else:
                target_id = self.search_keyword_1.selected_result["ID"]
                comp = self._get_or_create_subform("Clients")
                if hasattr(comp, "set_filter"):
                    comp.set_filter(target_id)
                else:
                    from ..ClientContactReport import ClientContactReport
                    comp = ClientContactReport(target_id)
                self._mount_report(load_seq, selected, comp)

        elif selected == "Technicians":
            if selected_id is None:
                Notification("Technician is not found. Enter correct name of the technician", title="Missing Technician Details", style="danger", timeout=3).show()
                self.card_panel.clear()
                self.card_panel.visible = False
            else:
                comp = self._get_or_create_subform("Technicians")
                self._mount_report(load_seq, selected, comp)

        elif selected == "Staffs":
            if selected_id is None:
                Notification("Staff is not found. Enter correct name of the staff", title="Missing Staff Details", style="danger", timeout=3).show()
                self.card_panel.clear()
                self.card_panel.visible = False
            else:
                target_id = self.search_keyword_1.selected_result["ID"]
                comp = self._get_or_create_subform("Staffs")
                if hasattr(comp, "set_filter"):
                    comp.set_filter(target_id)
                else:
                    from ..StaffDetailsReport import StaffDetailsReport
                    comp = StaffDetailsReport(target_id)
                self._mount_report(load_seq, selected, comp)
                
       