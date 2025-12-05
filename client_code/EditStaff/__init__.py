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
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()

        set_default_error_handling(
            self.handle_server_errors
        )  # Set global server error handler
        

        # Set focus to search client
        self.txt_StaffName.focus()

        
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

    def btn_Search_click(self, **event_args):
        """Return staff records to drop down component."""
        valueName = self.txt_StaffName.text
        if valueName:
            self.drop_down_selectName.items = anvil.server.call("getStaffByName", valueName)
        else:
            alert("Sorry, please enter staff name to procced", title="Blank Field(s) Found")
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
            alert("Please select staff's name to proceed.", large=False)
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
            alert("Please enter staff's fullname.")
            self.txt_name.focus()
            self.btn_Update.enabled = True
            return
        elif any(char.isdigit() for char in name):
            alert("Full name should not contain any numbers.")
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_Update.enabled = True
            return
            """
        elif not phone:
            alert("Please enter staff's phone number.")
            self.txt_phone.focus()
            self.btn_Update.enabled = True
            return
        elif not re.match(
            r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$", phone
        ):
            alert("Please enter a valid phone number")
            self.txt_phone.text = ""
            self.txt_phone.focus()
            self.btn_Update.enabled = True
            return
            """
        elif not archived:
            alert("Please select active status.")
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
        alert("Staff updated successfully.", title="Success", large=False)

        # Clear form
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
