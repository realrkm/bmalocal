from ._anvil_designer import RowTemplate14Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...EditUserAccounts import EditUserAccounts
from ...ResetForgotPassword import ResetForgotPassword


class RowTemplate14(RowTemplate14Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def btn_Edit_click(self, **event_args):
        """This method is called when the button is clicked"""
        items = list(self.parent.items)
        alert(content=EditUserAccounts(items[list(self.parent.items).index(self.item)]), buttons=[], dismissible=False, large=True)

    def btn_ResetForgotPassword_click(self, **event_args):
        """This method is called when the button is clicked"""
        items = list(self.parent.items)
        alert(content=ResetForgotPassword(items[list(self.parent.items).index(self.item)]), buttons=[], dismissible=False, large=True)

    