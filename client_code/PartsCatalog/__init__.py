from ._anvil_designer import PartsCatalogTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
# Imports for iframe
from anvil.js.window import jQuery
from anvil.js import get_dom_node

class PartsCatalog(PartsCatalogTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        # Create an iframe element and set the src
        iframe = jQuery("<iframe width='100%' height='800px'>").attr("src","https://www.realoem.com/")
    
        # Append the iframe to a container in our form
        iframe.appendTo(get_dom_node(self.content_panel))
    
        