from ._anvil_designer import PeriodicPaymentTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class PeriodicPayment(PeriodicPaymentTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.repeating_panel_1.items = anvil.server.call("get_client_payment_summary")

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Search.enabled = False   # disable button while searching
        try:
            startDate = self.date_picker_start.date
            endDate = self.date_picker_end.date
            search_term = self.txt_SearchTerm.text

            # 1. No filters selected
            if not startDate and not endDate and not search_term:
                alert("Sorry, please select a date range, search term or both to proceed.",
                      title="Blank Field(s) Found", large=False)
                return

            # 2. Only one date selected
            if (startDate and not endDate) or (endDate and not startDate):
                alert("Please select both start and end dates to proceed.",
                      title="Missing Date", large=False)
                return

            # 3. Both dates provided but startDate > endDate
            if startDate and endDate and startDate > endDate:
                alert("Sorry, end date should be greater or equal to start date.",
                      title="Date Mismatch", large=False)
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
                alert("No payment details found for the selected filters.",
                      title="No Results", large=False)
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
            alert("No data to export.")
            return

        excel_file = anvil.server.call("export_client_payment_details", rows)
        anvil.media.download(excel_file)

