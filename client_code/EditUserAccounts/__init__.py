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
        alert(items)
        self.txt_email.text = items["email"]
        self.drop_down_role.selected_value = items["role"]
        self.drop_down_active.selected_value = items["enabled"]

    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        pass

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

