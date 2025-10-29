from ._anvil_designer import EditUserAccountsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class EditUserAccounts(EditUserAccountsTemplate):
    def __init__(self, items, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.drop_down_role.items  = anvil.server.call("get_account_roles")
        
        self.label_oldemail.text = items["email"]
        self.txt_email.text = items["email"]
        self.drop_down_role.selected_value = anvil.server.call("get_role_id", items["role"])
        self.drop_down_active.selected_value = items["enabled"]
        self.text_box_login_attempts.text = anvil.server.call("getFailedAttempts", items["email"])

    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        oldemail = self.label_oldemail.text
        email = self.txt_email.text.strip()
        role = self.drop_down_role.selected_value
        active = True if self.drop_down_active.selected_value == "Yes" else False
    
        # Validate inputs
        if not email:
            alert("Email is required.", title="Error", large=False)
            return
        if not role:
            alert("Role is required.", title="Error", large=False)
            return
        if active not in [True, False]:
            alert("Active status is required.", title="Error", large=False)
            return
    
        # Call server
        anvil.server.call(
            "update_user",
            email=oldemail,
            new_email=email,
            enabled=active,
            role_id=role,
        )
    
        alert("Update is successful", title="Success", large=False)
        self.btn_Close_click()
        get_open_form().btn_Settings_click()

            
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

