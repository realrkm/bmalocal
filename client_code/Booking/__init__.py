from ._anvil_designer import BookingTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class Booking(BookingTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')#Set focus into technician

    def btn_SearchCustomer_click(self, **event_args):
        """This method is called when the button is clicked"""
        valueCustomer = self.txt_ClientName.text
        if valueCustomer is None:
            alert("Enter Customer's name to proceed", title="Blank Field Found")
            return
        else:
            result = anvil.server.call("getClientFullnameFromSearchWord", valueCustomer)
            self.drop_down_selectCustomer.items = result

    def drop_down_selectCustomer_change(self, **event_args):
        """This method is called when an item is selected"""
        if self.drop_down_selectCustomer.selected_value:
            alert(self.drop_down_selectCustomer.selected_value)
        #results = anvil.server.call("",self.drop_down_selectCustomer.selected_value)

        