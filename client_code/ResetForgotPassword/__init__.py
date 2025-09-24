from ._anvil_designer import ResetForgotPasswordTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class ResetForgotPassword(ResetForgotPasswordTemplate):
    def __init__(self, items, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call("replaceBanner")
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        
        self.txt_email.text = items["email"]
        
    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        email = self.txt_email.text.strip()
        password = self.txt_password.text.strip()
        
        # Validate inputs
        if not password:
            alert("Password is required.", title="Error", large=False)
            return
        # Call server
        anvil.server.call("reset_password", email, password)

        alert("Update is successful", title="Success", large=False)
        self.btn_Close_click()
        get_open_form().btn_Settings_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
