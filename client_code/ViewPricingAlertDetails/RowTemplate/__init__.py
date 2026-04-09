from ._anvil_designer import RowTemplateTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...UpdatePricingAmount import UpdatePricingAmount


class RowTemplate(RowTemplateTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        self.user = anvil.users.get_user()

        # Any code you write here will run before the form opens.

    def btn_EditItem_click(self, **event_args):
        """This method is called when the button is clicked"""
        items = list(self.parent.items)
        partNo = items[list(self.parent.items).index(self.item)]['PartNo']
        self.raise_event("x-close-parent")
        alert(content=UpdatePricingAmount(partNo), buttons=[], dismissible=False, large=True)
        
        # Refresh the repeating panel after the alert closes
        self.parent.items = anvil.server.call('getPartsWhereBuyingPriceExceedsSelling',self.user)
    
        # Signal the parent form to close if no items remain
        if not self.parent.items:
            


