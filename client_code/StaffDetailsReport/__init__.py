from ._anvil_designer import StaffDetailsReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class StaffDetailsReport(StaffDetailsReportTemplate):
    def __init__(self, staffID, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        self.refresh_staff_table(staffID)
        
    def refresh_staff_table(self, staffID):
        staffs = anvil.server.call("getStaffReport", staffID)
        self.client_repeater.items = staffs
