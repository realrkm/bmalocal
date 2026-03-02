from ._anvil_designer import TehniciansTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from ..EditTechnician import EditTechnician
from ..Toolkits import Toolkits
import re


class Tehnicians(TehniciansTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self.dropdown_toolkits.items = [(r["ToolkitName"], r) for r in anvil.server.call('get_toolkits', None)]
        set_default_error_handling(self.handle_server_errors) #Set global server error handler

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            self._show_notification(
                message="Connection to server lost. Please check your internet or try again later.",
                title="Disconnected",
                style="danger"
            )
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            self._show_notification(
                message="Please connect to the internet to proceed.",
                title="No Internet",
                style="warning"
            )
        else:
            self._show_notification(
                message=f"Unexpected error: {exc}",
                title="Error",
                style="danger"
            )

    def _show_notification(self, message, title="", style="danger", timeout=3):
        """
        Displays an Anvil Notification that auto-dismisses after `timeout` seconds.
    
        :param message: The notification body text.
        :param title:   The notification title.
        :param style:   'danger' | 'warning' | 'success' | 'info'
        :param timeout: Seconds before the notification disappears (default: 3).
        """
        notif = Notification(
            message,
            title=title,
            style=style,      # controls the colour — danger=red, warning=orange, success=green, info=blue
            timeout=timeout,  # auto-dismisses after this many seconds
        )
        notif.show()

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_SaveAndNew.enabled = False #Disable button to prevent multiple clicks
    
        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()
        if self.dropdown_toolkits.selected_value is None:
            toolkit = None
        else:
            toolkit = self.dropdown_toolkits.selected_value["ID"]
        
        # Validation
        if not name:
            alert("Please enter technician's full name.")
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return
        elif any(char.isdigit() for char in name):
            alert("Full name should not contain any numbers.")
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return
        elif not phone:
            alert("Please enter technician's phone number.")
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled =True
            return
        elif not re.match(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$', phone):
            alert("Please enter a valid phone number")
            self.txt_phone.text = ""
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled =True
            return
        elif not toolkit:
            alert("Please select assigned toolkit.")
            self.dropdown_toolkits.focus()
            self.btn_SaveAndNew.enabled =True
            return


        # Call server function
        duplicate = anvil.server.call('check_duplicate_contact', "Technician", phone)
        if duplicate:
            alert("Sorry, a technician with that phone number has already been added. Please enter another phone number.", title="Duplicate Phone Number", large=False)
            self.txt_phone.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return

        # Save data
        anvil.server.call('save_technician_data', name, phone, toolkit)
        alert("Technician saved successfully.")

        # Clear form
        self.clear_form_fields()

    def clear_form_fields(self):
        """Helper function to clear all form fields after saving"""
        self.txt_name.text = ""
        self.txt_phone.text = ""
        self.dropdown_toolkits.items = [(r["ToolkitName"], r) for r in anvil.server.call('get_toolkits', None)]
        self.dropdown_toolkits.selected_value = None

        # Reset focus to the first field
        self.txt_name.focus()

        # Re-enable Save button
        self.btn_SaveAndNew.enabled = True
            
    def btn_EditTechnician_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=EditTechnician(), buttons=[], dismissible=False,large=True)

    def btn_Toolkit_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=Toolkits(),buttons=[], dismissible=False,large=True)
