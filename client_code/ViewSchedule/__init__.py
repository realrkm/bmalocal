from ._anvil_designer import ViewScheduleTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class ViewSchedule(ViewScheduleTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        self.repeating_panel_1.items = anvil.server.call("get_monthly_schedule_pivot")

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        startDate = self.date_picker_start.date
        endDate = self.date_picker_end.date
       
        if startDate is None and endDate is None:
            alert("Sorry, please enter date period to proceed", title="Blank Field(s) Found")
            return
        elif startDate is None and endDate:
            alert("Sorry, please enter start date to proceed", title="Blank Field(s) Found")
            return
        elif startDate > endDate:
            alert("Sorry, start date cannot be greater than end date", title="Mismatch Dates")
            return
        else:
            self.repeating_panel_1.items = anvil.server.call("get_monthly_schedule_pivot", startDate, endDate)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

    def btn_Export_click(self, **event_args):
        rows = list(self.repeating_panel_1.items)

        if not rows:
            alert("No data to export.")
            return

        excel_file = anvil.server.call("export_monthly_schedule", rows)
        anvil.media.download(excel_file)

