from ._anvil_designer import SelfServiceTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class SelfService(SelfServiceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        #while anvil.users.get_user() is None:
        #    anvil.users.login_with_form()
        #result = anvil.server.call("update_carpart_categories")
        #alert(f"Updated {result['updated_rows']} rows")
        set_default_error_handling(self.handle_server_errors) #Set global server error handler

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)   
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def getCarPartNamesAndCategory(self):
        return anvil.server.call('getCarPartNamesAndCategory')

    def get_technician_jobcards_by_status(self):
        return anvil.server.call("get_technician_jobcards_by_status")

    def save_work_done(self, jobcardref, workdone):
        anvil.server.call("save_work_done_by_technician", jobcardref, workdone)
        return None

    def storeTechDetails(self, jobcard_ref, tech_notes, defect_list, parts_and_quantities ):
        anvil.server.call("storeTechDetails", jobcard_ref, tech_notes, defect_list, parts_and_quantities)
        return None