from ._anvil_designer import UserAccountsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class UserAccounts(UserAccountsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        rows = anvil.server.call("getUsers")
        self.repeating_panel_1.items = rows
      