from ._anvil_designer import WhatsAppTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
# Imports for iframe
from anvil.js.window import jQuery
from anvil.js import get_dom_node

class WhatsApp(WhatsAppTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        if self.txt_Client.text:
            self.drop_down_selectClient.items = anvil.server.call("getMatchingClient", self.txt_Client.text)
            
    def drop_down_selectClient_change(self, **event_args):
        """This method is called when an item is selected"""
        self.column_panel.visible =True
        phone = anvil.server.call_s("getClientPhoneNumber", self.drop_down_selectClient.selected_value)
        # Create an iframe element and set the src
        source = f"https://web.whatsapp.com/send?phone={phone}"
        iframe = jQuery("<iframe width='100%' height='800px'>").attr("src",source)

        # Append the iframe to a container in our form
        iframe.appendTo(get_dom_node(self.content_panel))
        
