from ._anvil_designer import PriceCatalogueTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..BuyingPrice import BuyingPrice
from ..MissingBuyingPrice import MissingBuyingPrice
from ..SellingPrice import SellingPrice
from ..MissingSellingPrice import MissingSellingPrice
import anvil.js

class PriceCatalogue(PriceCatalogueTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.repeating_panel_1.items = anvil.server.call("get_filtered_parts")
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_text = self.text_box_search.text.strip()

        if not search_text:
            alert("Please enter part name or part number to search.", title="Missing Part Details")
            self.text_box_search.focus()
            return

        result = anvil.server.call("get_filtered_parts", search_text)

        if result:
            # Clear drop down
            self.repeating_panel_1.items = ""
            self.repeating_panel_1.items = result
        else:
            alert("No records found for the entered part detail.", title="Not Found")

    def btn_BuyingPrice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_BuyingPrice.enabled = False
        alert(content=BuyingPrice(), buttons=[], dismissible=False,large=True)
        self.btn_BuyingPrice.enabled = True

    def btn_SellingPrice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_SellingPrice.enabled = False
        alert(content=SellingPrice(), buttons=[], dismissible=False,large=True)
        self.btn_SellingPrice.enabled = True
        
    def btn_MissingBuyingPrice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_MissingBuyingPrice.enabled = False
        alert(content=MissingBuyingPrice(), buttons=[], dismissible=False,large=True)
        self.btn_MissingBuyingPrice.enabled = True
        
    def btn_MissingSellingPrice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_MissingSellingPrice.enabled = False
        alert(content=MissingSellingPrice(), buttons=[], dismissible=False,large=True)
        self.btn_MissingSellingPrice.enabled = True

 
        
    
