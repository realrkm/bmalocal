from ._anvil_designer import AssignedJobCardsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class AssignedJobCards(AssignedJobCardsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()

        # Any code you write here will run before the form opens.
        self.repeating_panel_1.items = anvil.server.call('get_assigned_jobs', None, None, None)
        grandTotalInvoices = 0
        grandTotalLabour = 0
        for items in self.repeating_panel_1.items:
            grandTotalInvoices += float(items["InvoicedAmount"].replace(",",""))
            grandTotalLabour += float(items["LabourAmount"].replace(",",""))
        self.labelInvoiceTotal.text = f"{grandTotalInvoices:,.2f}"
        self.labelLabourTotal.text = f"{grandTotalLabour:,.2f}"

        self.drop_down_selectTechnician.items = anvil.server.call_s("getTechnicianInJobCard")
       
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Search.enabled = False   # disable button while searching
        try:
            startDate = self.date_picker_start.date
            endDate = self.date_picker_end.date
            technicianID = self.drop_down_selectTechnician.selected_value    
    
            # 1. No filters selected
            if not startDate and not endDate and not technicianID:
                alert("Sorry, please select a date range, technician or both to proceed.", 
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
                alert("No jobs found for the selected filters.", 
                    title="No Results", large=False)
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
            alert("No data to export.")
            return
       
        excel_file = anvil.server.call("export_assigned_jobcards", rows)
        anvil.media.download(excel_file)

            
        
        
        
