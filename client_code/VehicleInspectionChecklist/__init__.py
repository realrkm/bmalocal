from ._anvil_designer import VehicleInspectionChecklistTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class VehicleInspectionChecklist(VehicleInspectionChecklistTemplate):
    def __init__(self, jobcardid, **properties):
        # Set Form properties and Data Bindings.
        super().__init__(**properties)

        # Any code you write here will run before the form opens.

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
