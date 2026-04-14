from ._anvil_designer import TechniciansDetailsReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class TechniciansDetailsReport(TechniciansDetailsReportTemplate):
    def __init__(self,  **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        self.refresh_technician_table()
        
    def refresh_technician_table(self):
        technicians = anvil.server.call('getTechnicianReport', None)
        self.client_repeater.items = technicians

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_term = self.txt_Search.text.strip()

        if not search_term:
            alert("Please enter technician's name to search.", title="Missing Search Term")
            self.txt_Search.focus()
            return

        cardetails = anvil.server.call("getTechnicianReport", search_term)

        if cardetails:
            self.client_repeater.items = cardetails
        else:
            alert("No records found for the entered technician's name.", title="Not Found")