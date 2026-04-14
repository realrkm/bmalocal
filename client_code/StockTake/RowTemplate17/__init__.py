from ._anvil_designer import RowTemplate17Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class RowTemplate17(RowTemplate17Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def btn_DeleteRow_click(self, **event_args):
        """This method is called when the button is clicked"""
        items = list(self.parent.items)
        del items[list(self.parent.items).index(self.item)]
        
        # Re-number items
        for i, item in enumerate(items, start=1):
            item["No"] = i

        self.parent.items = items
