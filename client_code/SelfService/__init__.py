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
        #result = anvil.server.call("update_carpart_categories")
        #alert(f"Updated {result['updated_rows']} rows")
    def getCarPartNamesAndCategory(self):
        # Bridge method for HTML Panel
        return anvil.server.call('getCarPartNamesAndCategory')

    def get_technician_jobcards_by_status(self):
        return anvil.server.call("get_technician_jobcards_by_status")