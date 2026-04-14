from ._anvil_designer import StockTakingTipTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..CycleCountingProcedureTip import CycleCountingProcedureTip
from ..ReconcileInventoryTip import ReconcileInventoryTip

class StockTakingTip(StockTakingTipTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def btn_CycleCountingProcedure_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=CycleCountingProcedureTip(), buttons=[], dismissible=False, large=True)
    
    def btn_ReconcileInventory_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=ReconcileInventoryTip(), buttons=[], dismissible=False, large=True)
    
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)

    

    