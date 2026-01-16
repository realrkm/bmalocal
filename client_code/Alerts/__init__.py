from ._anvil_designer import AlertsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class Alerts(AlertsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.user = anvil.users.get_user()
        self.repeating_panel_1.items=anvil.server.call_s("fetch_active_notifications", self.user)

    @handle("btn_UpdateStatus", "click")
    def btn_UpdateStatus_click(self, **event_args):
        """This method is called when the button is clicked"""
        anvil.server.call_s("deactivate_notifications")
        alert("Pending statuses have been updated successfully", title="Success")
        self.raise_event("x-close-alert", value=True)
        
