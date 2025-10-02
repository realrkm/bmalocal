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
    
    def searchInvoices(self, **event_args):
        """This method is called when the button is clicked"""
        startDate = self.date_picker_start.date
        endDate = self.date_picker_end.date
        
        if startDate and endDate is None:
            pass #Do nothing
        elif startDate is None and endDate is None:
            alert("Sorry, please enter date period to proceed", title="Blank Field(s) Found")
            return
        elif startDate is None and endDate:
            alert("Sorry, please enter start date to proceed", title="Blank Field(s) Found")
            return
        elif startDate > endDate:
            alert("Sorry, start date cannot be greater than end date", title="Mismatch Dates")
            return
        else:
            self.drop_down_1.items = anvil.server.call("getMonthlyJobcardRef", startDate, endDate)

    def drop_down_1_change(self, **event_args):
        """This method is called when an item is selected"""
        startDate = self.date_picker_start.date
        endDate = self.date_picker_end.date
        jobcardrefID = self.drop_down_1.selected_value
        
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
            self.repeating_panel_1.items = anvil.server.call("getPeriodicInvoices", startDate, endDate, jobcardrefID)
            result = anvil.server.call("getFullnameInvoiceAmountAndBalance", jobcardrefID)
            self.lbl_ClientName.text=result["Fullname"]
            self.lbl_PaymentBalance.text=result["PaymentBal"]
            self.lbl_TotalInvoiceAmount.text=result["InvoiceTotal"]
   