from ._anvil_designer import EditTechnicianTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModNavigation
import re

class EditTechnician(EditTechnicianTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        
        self.dropdown_toolkits.items = [(r["ToolkitName"], r) for r in anvil.server.call('get_toolkits', None)]
        
        #Set focus to search client
        self.txt_technicianName.focus()
        
    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_Search_click(self,  **event_args):
        """Return technician records to drop down component."""
        valueName = self.txt_technicianName.text
        if valueName:
            self.drop_down_selectName.items = anvil.server.call('getTechnicianNameAndID', valueName)
        else:
<<<<<<< HEAD
            alert("Sorry, please enter technician name to proceed", title="Blank Field(s) Found")
=======
            Notification("Sorry, please enter technician name to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
>>>>>>> origin/main
            return
            
    def drop_down_selectName_change(self,  **event_args):
        """This method is called when an item is selected"""
        x = anvil.server.call('get_technician_details', self.drop_down_selectName.selected_value)
        self.txt_name.text = x[0]['Fullname']
        self.txt_phone.text = x[0]['Phone']
        tool = anvil.server.call_s('get_toolkits', x[0]["ToolkitID"])
        self.dropdown_toolkits.selected_value = tool[0]
        self.drop_down_archived.selected_value = x[0]["Active"]
        
        
    def btn_Update_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_Update.enabled = False #Disable button to prevent multiple clicks
        
        if self.drop_down_selectName.selected_value is None:
<<<<<<< HEAD
            alert("Please select technician's name to proceed.", large=False)
=======
            Notification("Please select technician's name to proceed.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.drop_down_selectName.focus()
            self.btn_Update.enabled =True
            return
        else:
            technician_id = self.drop_down_selectName.selected_value
            
        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()
        toolkit = self.dropdown_toolkits.selected_value
        archived = self.drop_down_archived.selected_value
        
        # Validation
        if not name:
<<<<<<< HEAD
            alert("Please enter technician's full name.")
=======
            Notification("Please enter technician's full name.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_name.focus()
            self.btn_Update.enabled =True
            return
        elif any(char.isdigit() for char in name):
<<<<<<< HEAD
            alert("Full name should not contain any numbers.")
=======
            Notification("Full name should not contain any numbers.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_Update.enabled =True
            return
        elif not phone:
<<<<<<< HEAD
            alert("Please enter technician's phone number.")
=======
            Notification("Please enter technician's phone number.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_phone.focus()
            self.btn_Update.enabled =True
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
            self.btn_Update.enabled =True
            return
            """
        elif not toolkit:
<<<<<<< HEAD
            alert("Please select toolkit.")
=======
            Notification("Please select toolkit.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.dropdown_toolkits.focus()
            self.btn_Update.enabled =True
            return
        elif not archived:
<<<<<<< HEAD
            alert("Please select active status.")
=======
            Notification("Please select active status.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.drop_down_archived.focus()
            self.btn_Update.enabled =True
            return

        if self.drop_down_archived.selected_value == "Yes":
            archived = 1
        else:
            archived = 0
            
        # Save data
        anvil.server.call('update_technician_data', name, phone, toolkit["ID"], archived, technician_id)
<<<<<<< HEAD
        alert("Technician updated successfully.", title="Success", large=False)
=======
        Notification("Technician updated successfully.", title="Success", style="success", timeout=3).show()
>>>>>>> origin/main

        # Clear form
        self.btn_Close_click()        

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)

    