from ._anvil_designer import PeriodicPaymentTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModGetData


class PeriodicPayment(PeriodicPaymentTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._rt_token = None
        self._is_mounted = True
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekPaymentSummaryCached", lambda: None)()
        if cached is not None:
            self.repeating_panel_1.items = cached
        else:
            anvil.js.window.setTimeout(self._load_initial_data, 0)

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            if hasattr(ModGetData, "getPaymentSummaryCached"):
                rows = ModGetData.getPaymentSummaryCached()
            else:
                rows = anvil.server.call("get_client_payment_summary")
        if self._is_mounted:
            self.repeating_panel_1.items = rows

    def _on_payments_changed(self, evt=None):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            start_date = self.date_picker_start.date
            end_date = self.date_picker_end.date
            search_term = (self.txt_SearchTerm.text or "").strip()
            if (start_date and not end_date) or (end_date and not start_date):
                start_date, end_date = None, None
            if not start_date and not end_date and not search_term and hasattr(ModGetData, "getPaymentSummaryCached"):
                rows = ModGetData.getPaymentSummaryCached(force_refresh=True)
            else:
                rows = anvil.server.call("get_client_payment_summary", search_term or None, start_date, end_date)
        if self._is_mounted:
            self.repeating_panel_1.items = rows

    def _unsubscribe_realtime(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt and self._rt_token:
                rt.unsubscribe(self._rt_token)
        except Exception:
            pass
        self._rt_token = None

    def form_show(self, **event_args):
        self._is_mounted = True
        self._unsubscribe_realtime()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_token = rt.subscribe("payments", self._on_payments_changed)
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
            search_term = self.txt_SearchTerm.text.strip()

            # 1. No filters selected
            if not startDate and not endDate and not search_term:
                Notification("Sorry, please select a date range, search term or both to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
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
            if startDate and endDate and not search_term:
                jobs = anvil.server.call("get_client_payment_summary", None, startDate, endDate)
            elif not startDate and not endDate and search_term:
                jobs = anvil.server.call("get_client_payment_summary", search_term)
            elif startDate and endDate and search_term:
                jobs = anvil.server.call("get_client_payment_summary", search_term,  startDate, endDate)
            else:
                jobs = []

            # 5. Handle empty results
            if not jobs:
                Notification("No payment details found for the selected filters.", title="No Results", style="warning", timeout=3).show()
                self.repeating_panel_1.items = []
                return

            # 6. If jobs found, update panel and totals
            self.repeating_panel_1.items = jobs

        finally:
            self.btn_Search.enabled = True   # re-enable button after processing

    def btn_Export_click(self, **event_args):
        """This method is called when the button is clicked"""
        rows = list(self.repeating_panel_1.items)

        if not rows:
            Notification("No data to export.", style="warning", timeout=3).show()
            return

        excel_file = anvil.server.call("export_client_payment_details", rows)
        anvil.media.download(excel_file)

