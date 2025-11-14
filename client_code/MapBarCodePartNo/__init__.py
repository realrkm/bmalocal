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
    
    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)

    def btn_AddNewPart_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=AddNewParts(isPopup=True),buttons=[], dismissible=True, large=True)

    def btn_Search_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        search_value = self.text_box_searchPartNo.text.strip()

        if not search_value:
            alert("Please enter part name or part no. to proceed.", title="Blank Field(s) Found", large=False)
            self.text_box_searchPartNo.focus()
            return

        result = anvil.server.call('getCarPartNameAndNumber', search_value)

        #Clear drop down 
        self.drop_down_selectPart.items = ""

        if result:
            self.drop_down_selectPart.items = result
        else:
            alert("No records found for the entered part detail.", title="Not Found")

    def drop_down_selectPart_change(self, **event_args):
        """This method is called when an item is selected"""
        result = anvil.server.call_s("getCarPartNumberWithID", self.drop_down_selectPart.selected_value)
        self.lbl_PartNumber.text = result[0]["PartNo"]
        self.refresh()
        
    def btn_Save_click(self, **event_args):
        """This method is called when the button is clicked"""
        barcode = self.txt_BarCode.text.strip()
        partNo = self.lbl_PartNumber.text.strip()

        if not barcode:
            alert("Sorry, please enter barcode / partno details", large=False)
            self.txt_BarCode.focus()
            return

        if not partNo:
            alert("Sorry, please select partno details", large=False)
            self.text_box_searchPartNo.focus()
            return

        result = anvil.server.call("saveBarcodePartNo", barcode,partNo)
        alert(f"{result}",title="Success", large=False)
        self.btn_Close_click()

        


