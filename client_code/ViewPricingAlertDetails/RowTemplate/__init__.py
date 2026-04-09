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
        # Pass partNo up to ViewPricingAlertDetails instead of opening a nested alert
        self.raise_event("x-close-parent", partNo=partNo)
        pricing_form = ViewPricingAlertDetails()
        alert(
            content=pricing_form,
            buttons=[],
            dismissible=False,
            large=True
        )
        # ViewPricingAlertDetails alert is now fully closed
        # Safe to open UpdatePricingAmount as a fresh top-level alert
        if pricing_form.selected_partNo:
            update_form = UpdatePricingAmount(pricing_form.selected_partNo)
            alert(
                content=update_form,
                buttons=[],
                dismissible=False,
                large=True
            )


