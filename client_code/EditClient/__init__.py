from ._anvil_designer import EditClientTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData
import re


class EditClient(EditClientTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self.txt_clientname.focus()

    def btn_Search_click(self, **event_args):
        """Search clients by name or phone."""
        if self.txt_clientname.text:
            self.drop_down_selectClient.items = anvil.server.call('getClientNameAndPhoneNumber', self.txt_clientname.text)
        else:
            Notification("Sorry, please enter client name to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            return

    def drop_down_selectClient_change(self, **event_args):
        """Populate client fields from RAM cache when warm, otherwise fetch by ID."""
        selected_id = self.drop_down_selectClient.selected_value
        if selected_id is None:
            return
        cached = getattr(ModGetData, "peekClientReportCached", lambda: None)()
        x = next((r for r in (cached or ()) if r.get("ID") == selected_id), None)
        if x is None:
            x = anvil.server.call('getClientNameWithID', selected_id)
        self.txt_name.text = x['Fullname']
        self.txt_phone.text = x['Phone']
        self.txt_address.text = x['Address']
        self.txt_email.text = x['Email']
        self.txt_narration.text = x['Narration']
    

    def btn_Update_click(self,  **event_args):
        """This method is called when the button is clicked"""
        self.btn_Update.enabled = False #Disable button to prevent multiple clicks 

        if self.drop_down_selectClient.selected_value is None:
            Notification("Please select client's name to proceed.", style="warning", timeout=3).show()
            self.drop_down_selectClient.focus()
            self.btn_Update.enabled =True
            return
        else:
            client_id = self.drop_down_selectClient.selected_value
            
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
            Notification("Please enter client's full name.", style="warning", timeout=3).show()
            self.txt_name.focus()
            self.btn_Update.enabled =True
            return
        elif any(char.isdigit() for char in name):
            Notification("Full name should not contain any numbers.", style="warning", timeout=3).show()
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_Update.enabled =True
            return
        elif not phone:
            Notification("Please enter client's phone number.", style="warning", timeout=3).show()
            self.txt_phone.focus()
            self.btn_Update.enabled =True
            return
            """
        elif not re.match(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$', phone):
            Notification("Please enter a valid phone number", timeout=3).show()
            self.txt_phone.text = ""
            self.txt_phone.focus()
            self.btn_Update.enabled =True
            return
            """
        # Update data     
        anvil.server.call('updateClientDetails', client_id, name, phone, address, email, narration)
        Notification("Client updated successfully.", title="Success", style="success", timeout=3).show()

        # Clear form
        self.btn_Close_click()        

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)

    