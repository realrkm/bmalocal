from ._anvil_designer import EditSupplierTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
import re


class EditSupplier(EditSupplierTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors)  # Set global server error handler
        
        self.drop_down_select.items = anvil.server.call("getSupplier")

              
    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert(
                "Connection to server lost. Please check your internet or try again later.",
                title="Disconnected",
                large=False,
            )
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert(
                "Please connect to the internet to proceed.",
                title="No Internet",
                large=False,
            )
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def drop_down_select_change(self,  **event_args):
        """This method is called when an item is selected"""
        x = anvil.server.call("getSupplierDetails", self.drop_down_select.selected_value)
        self.txt_name.text = x["Name"]
        self.txt_phone.text = x["Phone"]
        

    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Update.enabled = False  # Disable button to prevent multiple clicks

        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()

        # Validation
        if not name:
            alert("Please enter supplier's full name.")
            self.txt_name.focus()
            self.btn_Update.enabled = True
            return
        elif any(char.isdigit() for char in name):
            alert("Full name should not contain any numbers.")
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_Update.enabled = True
            return
        elif not phone:
            alert("Please enter supplier's phone number.")
            self.txt_phone.focus()
            self.btn_Update.enabled = True
            return

        # Update data
        anvil.server.call("updateSupplier",  name, phone, self.drop_down_select.selected_value)
        alert("Supplier updated successfully.", title="Success", large=False)

        # Clear form
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
        
