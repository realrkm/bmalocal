from ._anvil_designer import StockTakeTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.js import window, report_exceptions
from ..StockTakingTip import StockTakingTip 
from ..MapBarCodePartNo import MapBarCodePartNo

class StockTake(StockTakeTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        alert(content=StockTakingTip(), buttons=[], dismissible=False, large=True)
        self.repeating_panel_1.items = []   # start with empty list
        
        # Wrap callback so errors show in Anvil logs
        @report_exceptions
        def _display_result_from_js(result_text):
            # Show result directly in txt_barcode
            self.txt_BarcodePartNo.text = result_text
            self.add_part(result_text)

            # Auto-stop scanner after first successful scan
            if hasattr(window, "stopScanner"):
                window.stopScanner()

        # Expose callback to JS
        window.display_result = _display_result_from_js
        self._js_display_ref = _display_result_from_js

    def form_hide(self, **event_args):
        """Clean up when form closes"""
        try:
            window.display_result = None
        except Exception:
            pass

    def button_start_click(self, **event_args):
        """Start scanner when button is clicked"""
        # Clear previous result before scanning again
        self.txt_BarcodePartNo.text = ""
       
        if hasattr(window, "startScanner"):
            window.stopScanner()
            window.startScanner()
        else:
            alert("Scanner not ready – JS not loaded.")

    def button_stop_click(self, **event_args):
        """Stop scanner when button is clicked manually"""
        if hasattr(window, "stopScanner"):
            window.stopScanner()
        else:
            alert("Stop scanner not available.")

    def add_part(self, barcode_or_partno):
        value = str(barcode_or_partno).strip()
            
        items = list(self.repeating_panel_1.items or [])
    
        # Call server to resolve the part (or None if not found)
        part_info = anvil.server.call("resolve_part", value)
    
        if not part_info:
            # If not found in database → open mapping form
            alert(MapBarCodePartNo(barcode_or_partno=value), buttons=[], dismissible=False, large=True)
            #When MapBarCodePartNo is closed without mapping, the form keeps appearing, hence need to comment below code 
            #self.btn_AddPart_click() #Display the added barcode item in the repeating panel
            return
            
        # If repeating panel is empty → just add the item
        if not items:
            items.append({
                "No": 1,
                "Item": part_info["Name"],
                "PartNo": part_info["PartNo"],
                "Quantity": 1
            })
        else:
            # Check if the resolved part already exists in the repeating panel
            found = False
            for item in items:
                if item["PartNo"] == part_info["PartNo"]:
                    item["Quantity"] += 1
                    found = True
                    break
    
            # If not found → add as new item
            if not found:
                items.append({
                    "No": len(items) + 1,
                    "Item": part_info["Name"],
                    "PartNo": part_info["PartNo"],
                    "Quantity": 1
                })
    
        # Re-number items
        for i, item in enumerate(items, start=1):
            item["No"] = i
    
        self.repeating_panel_1.items = items

    def btn_AddPart_click(self, **event_args):
    # Triggered when "ADD PART" button is clicked
        barcode_or_partno = self.txt_BarcodePartNo.text.strip()
        if not barcode_or_partno:
            alert("Please enter a Barcode or Part Number before adding.")
            return
    
        self.add_part(barcode_or_partno)
        self.txt_BarcodePartNo.text = ""  # clear entry

    def btn_Upload_click(self, **event_args):
        """This method is called when the button is clicked"""
        data = [item for item in self.repeating_panel_1.items]
        anvil.server.call("save_stocktake", data)
        alert("Stocktake saved successfully")
        self.repeating_panel_1.items = []   # clears repeating panel
        self.txt_BarcodePartNo.text = ""


   