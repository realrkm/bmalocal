from ._anvil_designer import BuyingPriceTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class BuyingPrice(BuyingPriceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self.repeating_panel_1.items = anvil.server.call("get_buying_prices")

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_text = self.text_box_search.text.strip()

        if not search_text:
            Notification("Please enter part name or part number to search.", title="Missing Part Details", style="danger", timeout=3).show()
            self.text_box_search.focus()
            return

        result = anvil.server.call(
            "get_buying_prices", search_text)

        if result:
            # Clear drop down
            self.repeating_panel_1.items = ""
            self.repeating_panel_1.items = result
        else:
            Notification("No records found for the entered part detail.", title="Not Found", style="danger", timeout=3).show()
        
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
