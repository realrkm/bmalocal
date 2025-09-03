from ._anvil_designer import EditUserAccountsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class EditUserAccounts(EditUserAccountsTemplate):
    def __init__(self, items, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        self.drop_down_role.items  = anvil.server.call("get_account_roles")
        
        self.label_oldemail.text = items["email"]
        self.txt_email.text = items["email"]
        self.drop_down_role.selected_value = anvil.server.call("get_role_id", items["role"])
        self.drop_down_active.selected_value = items["enabled"]

    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        oldemail = self.label_oldemail.text
        email = self.txt_email.text
        role = self.drop_down_role.selected_value
        
        if self.drop_down_active.selected_value == "Yes":
            active = True
        else:
            active = False
            
        if email and role and active:
            anvil.server.call_s("update_user", oldemail, email, role, active)
            alert("Update is successfull", title="Success", large=False)
            self.btn_Close_click()
            get_open_form().btn_Settings_click()
            
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

