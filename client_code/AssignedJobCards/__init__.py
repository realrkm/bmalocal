from ._anvil_designer import AssignedJobCardsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


class AssignedJobCards(AssignedJobCardsTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._rt_tokens = []
        self._is_mounted = True
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekAssignedJobcardsBootstrapCached", lambda: None)()
        if cached is not None:
            self._apply_bootstrap(cached)
        else:
            self.repeating_panel_1.items = []
            self.labelInvoiceTotal.text = "0.00"
            self.labelLabourTotal.text = "0.00"
            anvil.js.window.setTimeout(self._load_initial_data, 0)

    def _apply_bootstrap(self, bootstrap):
        data = bootstrap or {}
        self.repeating_panel_1.items = data.get("jobs", [])
        self.drop_down_selectTechnician.items = data.get("technicians", [])
        self.calculate_totals()

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            if hasattr(ModGetData, "getAssignedJobcardsBootstrapCached"):
                bootstrap = ModGetData.getAssignedJobcardsBootstrapCached()
            else:
                bootstrap = anvil.server.call('get_assigned_jobcards_bootstrap')
        if self._is_mounted:
            self._apply_bootstrap(bootstrap)

    def _unsubscribe_realtime(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                for tok in self._rt_tokens:
                    rt.unsubscribe(tok)
        except Exception:
            pass
        self._rt_tokens = []

    def form_show(self, **event_args):
        self._is_mounted = True
        self._unsubscribe_realtime()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_tokens = [
                    rt.subscribe("jobcards", self._on_data_changed),
                    rt.subscribe("payments", self._on_data_changed),
                ]
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._is_mounted = False
        self._unsubscribe_realtime()

    def _on_data_changed(self, evt=None):
        with anvil.server.no_loading_indicator:
            start_date = self.date_picker_start.date
            end_date = self.date_picker_end.date
            tech_id = self.drop_down_selectTechnician.selected_value
            if (start_date and not end_date) or (end_date and not start_date):
                start_date, end_date = None, None
            if not start_date and not end_date and not tech_id and hasattr(ModGetData, "getAssignedJobcardsBootstrapCached"):
                bootstrap = ModGetData.getAssignedJobcardsBootstrapCached(force_refresh=True)
                self._apply_bootstrap(bootstrap)
            else:
                jobs = anvil.server.call("get_assigned_jobs", start_date, end_date, tech_id) or []
                self.repeating_panel_1.items = jobs
                self.calculate_totals()
       
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Search.enabled = False   # disable button while searching
        try:
            startDate = self.date_picker_start.date
            endDate = self.date_picker_end.date
            technicianID = self.drop_down_selectTechnician.selected_value    
    
            # 1. No filters selected
            if not startDate and not endDate and not technicianID:
                Notification("Sorry, please select a date range, technician or both to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
                return
    
            # 2. Only one date selected
            if (startDate and not endDate) or (endDate and not startDate):
                Notification("Please select both start and end dates to proceed.", title="Missing Date", style="danger", timeout=3).show()
                return
    
            # 3. Both dates provided but startDate > endDate
            if startDate and endDate and startDate > endDate:
                Notification("Sorry, end date should be greater or equal to start date.", title="Date Mismatch", style="warning", timeout=3).show()
                return
    
            # 4. Fetch based on provided filters
            if startDate and endDate and not technicianID:
                jobs = anvil.server.call("get_assigned_jobs", startDate, endDate, None)
            elif not startDate and not endDate and technicianID:
                jobs = anvil.server.call("get_assigned_jobs", None, None, technicianID)
            elif startDate and endDate and technicianID:
                jobs = anvil.server.call("get_assigned_jobs", startDate, endDate, technicianID)
            else:
                jobs = []
    
            # 5. Handle empty results
            if not jobs:
                Notification("No jobs found for the selected filters.", title="No Results", style="warning", timeout=3).show()
                self.repeating_panel_1.items = []
                self.labelInvoiceTotal.text = "0.00"
                self.labelLabourTotal.text = "0.00"
                return
    
            # 6. If jobs found, update panel and totals
            self.repeating_panel_1.items = jobs
            self.calculate_totals()
    
        finally:
            self.btn_Search.enabled = True   # re-enable button after processing


    def calculate_totals(self, **event_args):
        grandTotalInvoices = 0
        grandTotalLabour = 0
        for items in self.repeating_panel_1.items:
            grandTotalInvoices += float(items["InvoicedAmount"].replace(",",""))
            grandTotalLabour += float(items["LabourAmount"].replace(",",""))
        self.labelInvoiceTotal.text = f"{grandTotalInvoices:,.2f}"
        self.labelLabourTotal.text = f"{grandTotalLabour:,.2f}"

    def btn_Export_click(self, **event_args):
        rows = list(self.repeating_panel_1.items)

        if not rows:
            Notification("No data to export.", style="warning", timeout=3).show()
            return
       
        excel_file = anvil.server.call("export_assigned_jobcards", rows)
        anvil.media.download(excel_file)

            
        
        
        
