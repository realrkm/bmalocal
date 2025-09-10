from ._anvil_designer import MapBarCodePartNoTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..AddNewParts import AddNewParts


class MapBarCodePartNo(MapBarCodePartNoTemplate):
    def __init__(self, barcode_or_partno, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
    
        # Any code you write here will run before the form opens.
        self.txt_BarCode.text = barcode_or_partno

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)

    def btn_AddNewPart_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Close_click()
        alert(content=AddNewParts(),buttons=[], dismissible=True, large=True)

