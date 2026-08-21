from ._anvil_designer import ViewPricingAlertDetailsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModNavigation
from ..UpdatePricingAmount import UpdatePricingAmount

class ViewPricingAlertDetails(ViewPricingAlertDetailsTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)

        anvil.js.call("replaceBanner")
        self.user = anvil.users.get_user()
        self.refresh()
        
    def refresh(self,**event_args):
        self.repeating_panel_1.items = anvil.server.call_s(
            "getPartsWhereBuyingPriceExceedsSelling", self.user
        )

    def open_edit_form(self, partNo):
        
        # Open next alert
        result = alert(
            content=UpdatePricingAmount(partNo),
            buttons=[],
            dismissible=False,
            large=True
        )
        if result:
            self.refresh()