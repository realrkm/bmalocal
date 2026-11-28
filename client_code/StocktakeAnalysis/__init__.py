from ._anvil_designer import StocktakeAnalysisTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class StocktakeAnalysis(StocktakeAnalysisTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Search.enabled = False
        try:
            startDate = self.date_picker_start.date
            endDate = self.date_picker_end.date
            part_no = self.txt_PartNo.text

            if not startDate and not endDate and not part_no:
                Notification("Sorry, please select a date range, part number or both to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
                return

            if (startDate and not endDate) or (endDate and not startDate):
                Notification("Please select both start and end dates to proceed.", title="Missing Date", style="danger", timeout=3).show()
                return

            if startDate and endDate and startDate > endDate:
                alert(f"Sorry, end date {endDate} should be greater or equal to start date {startDate}.", title="Date Mismatch", large=False)
                return

            from ..DisplayStocktakeAnalysis import DisplayStocktakeAnalysis
            if startDate and endDate and not part_no:
                alert(content=DisplayStocktakeAnalysis(start_date=startDate, end_date=endDate, partnumber=None), dismissible=False, large=True)
            elif not startDate and not endDate and part_no:
                alert(content=DisplayStocktakeAnalysis(start_date=None, end_date=None, partnumber=part_no), dismissible=False, large=True)
            elif startDate and endDate and part_no:
                alert(content=DisplayStocktakeAnalysis(start_date=startDate, end_date=endDate, partnumber=part_no), dismissible=False, large=True)
        finally:
            self.btn_Search.enabled = True

   