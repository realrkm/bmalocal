from ._anvil_designer import ClientTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import ModGetData
import anvil.js
from ..EditClient import EditClient
from .. import ModNavigation
import re

class Client(ClientTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_SaveAndNew.enabled = False #Disable button to prevent multiple clicks 
        
        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()
        if self.txt_address.text is not None:
            address = self.txt_address.text.strip()
        else:
            address = self.txt_address.text
        if self.txt_email.text is not None:
            email = self.txt_email.text.strip()
        else:
            email = self.txt_email.text
        narration = self.txt_narration.text
    
        # Validation
        if not name:
<<<<<<< HEAD
            alert("Please enter client's full name.")
=======
            Notification("Please enter client's full name.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return
        elif any(char.isdigit() for char in name):
<<<<<<< HEAD
            alert("Full name should not contain any numbers.")
=======
            Notification("Full name should not contain any numbers.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return
        elif not phone:
<<<<<<< HEAD
            alert("Please enter client's phone number.")
=======
            Notification("Please enter client's phone number.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled =True
            return
        """
        elif not re.match(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$', phone):
<<<<<<< HEAD
            alert("Please enter a valid phone number")
=======
            Notification("Please enter a valid phone number", timeout=3).show()
>>>>>>> origin/main
            self.txt_phone.text = ""
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled =True
            return
        """               
        
        # Call server function
        duplicate = anvil.server.call('check_duplicate_contact', "Client", phone)
        if duplicate:
<<<<<<< HEAD
            alert("Sorry, a client with that phone number has already been added. Please enter another phone number", title="Duplicate Phone Number", large=False)
=======
            Notification("Sorry, a client with that phone number has already been added. Please enter another phone number", title="Duplicate Phone Number", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_phone.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return

        # Save data     
        anvil.server.call('save_client_data', name, phone, address, email, narration)
<<<<<<< HEAD
        alert("Client saved successfully.")
=======
        Notification("Client saved successfully.", style="warning", timeout=3).show()
>>>>>>> origin/main
        
        # Clear form
        self.clear_form_fields()                     

    def clear_form_fields(self):
        """Helper function to clear all form fields after saving"""
        self.txt_name.text = ""
        self.txt_phone.text = ""
        self.txt_address.text = ""
        self.txt_email.text = ""
        self.txt_narration.text = ""
    
        # Reset focus to the first field
        self.txt_name.focus()

        # Re-enable Save button in case it was disabled
        self.btn_SaveAndNew.enabled = True
    
    def btn_EditClient_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=EditClient(), buttons=[], dismissible=False,large=True)

