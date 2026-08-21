from ._anvil_designer import EditStaffTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModNavigation
import re


class EditStaff(EditStaffTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')

        # Set focus to search client
        self.txt_StaffName.focus() 
        
    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_Search_click(self, **event_args):
        """Return staff records to drop down component."""
        valueName = self.txt_StaffName.text
        if valueName:
            self.drop_down_selectName.items = anvil.server.call("getStaffByName", valueName)
        else:
<<<<<<< HEAD
            alert("Sorry, please enter staff name to procced", title="Blank Field(s) Found")
=======
            Notification("Sorry, please enter staff name to procced", title="Blank Field(s) Found", style="warning", timeout=3).show()
>>>>>>> origin/main
            return
            
    def drop_down_selectName_change(self,  **event_args):
        """This method is called when an item is selected"""
        x = anvil.server.call("get_staff_details", self.drop_down_selectName.selected_value)
        self.txt_name.text = x[0]["Fullname"]
        self.txt_phone.text = x[0]["Phone"]
        self.drop_down_archived.selected_value = x[0]["Active"]
        

    def btn_Update_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_Update.enabled = False  # Disable button to prevent multiple clicks


        if self.drop_down_selectName.selected_value is None:
<<<<<<< HEAD
            alert("Please select staff's name to proceed.", large=False)
=======
            Notification("Please select staff's name to proceed.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.drop_down_selectName.focus()
            self.btn_Update.enabled = True
            return
        else:
            staff_id = self.drop_down_selectName.selected_value
        
        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()
        archived = self.drop_down_archived.selected_value


        # Validation
        if not name:
<<<<<<< HEAD
            alert("Please enter staff's fullname.")
=======
            Notification("Please enter staff's fullname.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_name.focus()
            self.btn_Update.enabled = True
            return
        elif any(char.isdigit() for char in name):
<<<<<<< HEAD
            alert("Full name should not contain any numbers.")
=======
            Notification("Full name should not contain any numbers.", style="warning", timeout=3).show()
>>>>>>> origin/main
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_Update.enabled = True
            return
            """
        elif not phone:
<<<<<<< HEAD
            alert("Please enter staff's phone number.")
=======
            Notification("Please enter staff's phone number.", timeout=3).show()
>>>>>>> origin/main
            self.txt_phone.focus()
            self.btn_Update.enabled = True
            return
        elif not re.match(
            r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$", phone
        ):
<<<<<<< HEAD
            alert("Please enter a valid phone number")
=======
            Notification("Please enter a valid phone number", timeout=3).show()
>>>>>>> origin/main
            self.txt_phone.text = ""
            self.txt_phone.focus()
            self.btn_Update.enabled = True
            return
            """
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
        anvil.server.call(
            "update_staff_data", name, phone, archived, staff_id
        )
<<<<<<< HEAD
        alert("Staff updated successfully.", title="Success", large=False)
=======
        Notification("Staff updated successfully.", title="Success", style="success", timeout=3).show()
>>>>>>> origin/main

        # Clear form
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
