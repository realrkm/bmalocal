from ._anvil_designer import ViewPricingAlertDetailsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModNavigation


class ViewPricingAlertDetails(ViewPricingAlertDetailsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call("replaceBanner")
        self.user = anvil.users.get_user()
        self.repeating_panel_1.items = anvil.server.call_s(
            "getPartsWhereBuyingPriceExceedsSelling", self.user
        )
        self.repeating_panel_1.set_event_handler("x-close-parent", self.Close_click)

    def Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
