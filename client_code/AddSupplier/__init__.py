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
        anvil.js.call('replaceBanner')
        
    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_SaveAndNew.enabled = False  # Disable button to prevent multiple clicks

        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()
    
        # Validation
        if not name:
<<<<<<< HEAD
            alert("Please enter supplier's full name.")
=======
            Notification("Please enter supplier's full name.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return
        elif any(char.isdigit() for char in name):
<<<<<<< HEAD
            alert("Full name should not contain any numbers.")
=======
            Notification("Full name should not contain any numbers.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return
        elif not phone:
<<<<<<< HEAD
            alert("Please enter suppliers's phone number.")
=======
            Notification("Please enter suppliers's phone number.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled = True
            return
       

        # Call server function
        duplicate = anvil.server.call("check_duplicate_contact", "Supplier", phone)
        if duplicate:
<<<<<<< HEAD
            alert(
                "Sorry, a supplier with that phone number has already been added. Please enter another phone number",
                title="Duplicate Phone Number",
                large=False,
            )
=======
            Notification("Sorry, a supplier with that phone number has already been added. Please enter another phone number", title="Duplicate Phone Number", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_phone.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return

        # Save data
        anvil.server.call("addSupplier", name, phone)
<<<<<<< HEAD
        alert("Supplier saved successfully.")
=======
        Notification("Supplier saved successfully.", style="warning", timeout=3).show()
>>>>>>> origin/main
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
        get_open_form().btn_Inventory_click()

