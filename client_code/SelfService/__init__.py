from ._anvil_designer import SelfServiceTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class SelfService(SelfServiceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        self.call_from_js()
    def call_from_js(self):
        # Calls the server function from the client
        #result = anvil.server.call('getCarPartNamesAndCategory')
        #return result
        alert("Hello,Tom")
        return 42