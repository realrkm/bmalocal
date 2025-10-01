from ._anvil_designer import MonthlyPerformanceScheduleTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class MonthlyPerformanceSchedule(MonthlyPerformanceScheduleTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
    
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        startDate = self.date_picker_start.date
        endDate = self.date_picker_end.date
        searchTerm = self.txt_JobCardRef.text

        if not startDate or not endDate:
            alert("Sorry, please enter date period to proceed", title="Blank Field(s) Found")
            return
        if startDate > endDate:
            alert("Sorry, start date cannot be greater than end date", title="Mismatch Dates")
            return
        if not searchTerm:
            alert("Sorry, please enter job card ref to proceed", title="Blank Field(s) Match")
            self.txt_JobCardRef.focus()
            return
            
        self.repeating_panel_1.items = anvil.server.call("getPeriodicInvoices", startDate, endDate, searchTerm)
