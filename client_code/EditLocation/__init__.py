from ._anvil_designer import EditLocationTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class EditLocation(EditLocationTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self.drop_down_select.items = anvil.server.call("getLocation")

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def drop_down_select_change(self, **event_args):
        """This method is called when an item is selected"""
        self.txt_name.text = anvil.server.call("getLocationName", self.drop_down_select.selected_value)

    def btn_Update_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_Update.enabled = False  # Disable button to prevent multiple clicks
        name = self.txt_name.text.strip().upper()
        id = self.drop_down_select.selected_value
        # Validation
        if not name:
            alert("Please enter location name.")
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return

        # Save data
        anvil.server.call("updateLocation", name, id)
        alert("Location updated successfully.")

        # Clear form
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
        

    