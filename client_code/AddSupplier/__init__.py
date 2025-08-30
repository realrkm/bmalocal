from ._anvil_designer import AddSupplierTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from ..EditSupplier import EditSupplier
from .. import ModNavigation
import re


class AddSupplier(AddSupplierTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call("replaceBanner")

        set_default_error_handling(
            self.handle_server_errors
        )  # Set global server error handler

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

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_SaveAndNew.enabled = False  # Disable button to prevent multiple clicks

        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()
    
        # Validation
        if not name:
            alert("Please enter supplier's full name.")
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return
        elif any(char.isdigit() for char in name):
            alert("Full name should not contain any numbers.")
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return
        elif not phone:
            alert("Please enter suppliers's phone number.")
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled = True
            return
       

        # Call server function
        duplicate = anvil.server.call("check_duplicate_contact", "Supplier", phone)
        if duplicate:
            alert(
                "Sorry, a supplier with that phone number has already been added. Please enter another phone number",
                title="Duplicate Phone Number",
                large=False,
            )
            self.txt_phone.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return

        # Save data
        anvil.server.call("addSupplier", name, phone)
        alert("Supplier saved successfully.")
        self.btn_SaveAndNew.enabled = True
        
        # Clear form
        self.txt_name.text = ""
        self.txt_phone.text=""

    def btn_EditSupplier_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=EditSupplier(), buttons=[], dismissible=False, large=True)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)
        get_open_form().btn_Inventory_click("AddNewParts")

