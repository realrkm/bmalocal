from ._anvil_designer import DefectsFormTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


class DefectsForm(DefectsFormTemplate):
    def __init__(self, defects_data=None, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call("replaceBanner")
        set_default_error_handling(self.handle_server_errors)  # Set global server error handler

        self.populateForm(defects_data)

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.",title="Disconnected",large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.",title="No Internet",large=False)
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def populateForm(self, defects_data, **event_args):
        """This method is called when an item is selected"""   
        self.txtClientInstructions.text = ModGetData.getJobCardInstructions(defects_data[0]["ID"])
        self.txtTechNotes.text = ModGetData.getJobCardTechNotes(defects_data[0]["ID"])
        self.txtDefectsList.text = anvil.server.call_s('getJobCardDefects',defects_data[0]["ID"])
        self.txtRequestedParts.text = anvil.server.call_s('getRequestedParts',defects_data[0]["ID"])

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
