from ._anvil_designer import Form1Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class Form1(Form1Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        user = anvil.users.get_user()
        if user:
            # Fetch details
            self.repeating_panel_1.items = anvil.server.call("get_filtered_parts")
        #self.data_grid_1.role='wide'
