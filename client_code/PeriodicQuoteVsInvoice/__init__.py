from ._anvil_designer import PeriodicQuoteVsInvoiceTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModGetData


class PeriodicQuoteVsInvoice(PeriodicQuoteVsInvoiceTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._rt_tokens = []
        self._is_mounted = True
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekQuoteInvoiceTotalsCached", lambda: None)()
        if cached is not None:
            self.repeating_panel_1.items = cached
        else:
            anvil.js.window.setTimeout(self._load_initial_data, 0)

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            if hasattr(ModGetData, "getQuoteInvoiceTotalsCached"):
                rows = ModGetData.getQuoteInvoiceTotalsCached()
            else:
                rows = anvil.server.call("get_jobcard_quote_invoice_totals")
        if self._is_mounted:
            self.repeating_panel_1.items = rows

    def _on_realtime_changed(self, evt=None):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            start_date = self.date_picker_start.date
            end_date = self.date_picker_end.date
            job_ref = (self.txt_JobCardRef.text or "").strip()
            if (start_date and not end_date) or (end_date and not start_date):
                start_date, end_date = None, None
            if not start_date and not end_date and not job_ref and hasattr(ModGetData, "getQuoteInvoiceTotalsCached"):
                rows = ModGetData.getQuoteInvoiceTotalsCached(force_refresh=True)
            else:
                rows = anvil.server.call("get_jobcard_quote_invoice_totals", job_ref or None, start_date, end_date)
        if self._is_mounted:
            self.repeating_panel_1.items = rows

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
                    rt.subscribe("jobcards", self._on_realtime_changed),
                    rt.subscribe("payments", self._on_realtime_changed),
                ]
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._is_mounted = False
        self._unsubscribe_realtime()

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Search.enabled = False   # disable button while searching
        try:
            startDate = self.date_picker_start.date
            endDate = self.date_picker_end.date
            jobCardRef = self.txt_JobCardRef.text   

            # 1. No filters selected
            if not startDate and not endDate and not jobCardRef:
                Notification("Sorry, please select a date range, job card ref or both to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
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
            if startDate and endDate and not jobCardRef:
                jobs = anvil.server.call("get_jobcard_quote_invoice_totals", None, startDate, endDate)
            elif not startDate and not endDate and jobCardRef:
                jobs = anvil.server.call("get_jobcard_quote_invoice_totals", jobcard_ref = self.txt_JobCardRef.text)
            elif startDate and endDate and jobCardRef:
                jobs = anvil.server.call("get_jobcard_quote_invoice_totals", jobCardRef,  startDate, endDate)
            else:
                jobs = []

            # 5. Handle empty results
            if not jobs:
                Notification("No job cards found for the selected filters.", title="No Results", style="warning", timeout=3).show()
                self.repeating_panel_1.items = []
                return

            # 6. If jobs found, update panel and totals
            self.repeating_panel_1.items = jobs

        finally:
            self.btn_Search.enabled = True   # re-enable button after processing

