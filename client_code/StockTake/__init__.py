from ._anvil_designer import StockTakeTemplate
from anvil import *
from anvil.js import window, report_exceptions

class StockTake(StockTakeTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
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
        # Convert to string for uniformity
        value = str(barcode_or_partno).strip()
        if not value:
            return

        items = list(self.repeating_panel_1.items or [])

        # Check if the value already exists (by PartNo or Barcode)
        found = False
        for item in items:
            if item["PartNo"] == value or item["Barcode"] == value:
                item["Quantity"] += 1
                found = True
                break

        if not found:
            # Add as a new row
            items.append({
                "No": len(items) + 1,
                "Item": "Part Description",  # you can fetch description if needed
                "PartNo": value,
                "Barcode": value,
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

   