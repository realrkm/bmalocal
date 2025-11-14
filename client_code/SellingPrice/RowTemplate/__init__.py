from ._anvil_designer import RowTemplateTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...UpdateBuyingAndSellingPrice import UpdateBuyingAndSellingPrice


class RowTemplate(RowTemplateTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def btn_Edit_click(self, **event_args):
        """This method is called when the button is clicked"""
        items = list(self.parent.items)
        self.parent.raise_event('x-close-alert', value=True)
        alert(content=UpdateBuyingAndSellingPrice(items[list(self.parent.items).index(self.item)], "Selling"),buttons=[],dismissible=False, large=True)


