from ._anvil_designer import PeriodicQuoteVsInvoiceTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js

class PeriodicQuoteVsInvoice(PeriodicQuoteVsInvoiceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self._rt_tokens = []
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)
        anvil.js.window.setTimeout(self._load_initial_data, 10)

    def _load_initial_data(self):
        with anvil.server.no_loading_indicator:
            self.repeating_panel_1.items = anvil.server.call("get_jobcard_quote_invoice_totals")

    def form_show(self, **event_args):
        self.form_hide()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_tokens = [
                    rt.subscribe("jobcards", lambda evt: self._load_initial_data()),
                    rt.subscribe("payments", lambda evt: self._load_initial_data()),
                ]
        except Exception:
            pass

    def form_hide(self, **event_args):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                for tok in self._rt_tokens:
                    rt.unsubscribe(tok)
        except Exception:
            pass
        self._rt_tokens = []

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

