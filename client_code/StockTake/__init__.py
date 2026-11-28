from ._anvil_designer import StockTakeTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.js import window, report_exceptions


class StockTake(StockTakeTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self.repeating_panel_1.items = []   # start with empty list
        self._tip_shown = False
        self._prewarmed_tip = None

        # Wrap callback so errors show in Anvil logs
        @report_exceptions
        def _display_result_from_js(result_text):
            self.txt_BarcodePartNo.text = result_text
            self.add_part(result_text)
            if hasattr(window, "stopScanner"):
                window.stopScanner()

        self._js_display_ref = _display_result_from_js
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)
        try:
            window.setTimeout(self._prewarm_tip_modal, 15)
        except Exception:
            pass

    def _prewarm_tip_modal(self):
        if self._tip_shown or self._prewarmed_tip is not None:
            return
        try:
            from ..StockTakingTip import StockTakingTip
            self._prewarmed_tip = StockTakingTip()
        except Exception:
            self._prewarmed_tip = None

    def _open_tip_if_needed(self):
        if self._tip_shown:
            return
        self._tip_shown = True
        tip = self._prewarmed_tip
        self._prewarmed_tip = None
        if tip is None:
            from ..StockTakingTip import StockTakingTip
            tip = StockTakingTip()
        alert(content=tip, buttons=[], dismissible=False, large=True)

    def form_show(self, **event_args):
        """Attach scanner callback and show StockTakingTip once StockTake is mounted."""
        try:
            window.display_result = self._js_display_ref
        except Exception:
            pass
        if not self._tip_shown:
            try:
                window.setTimeout(self._open_tip_if_needed, 0)
            except Exception:
                self._open_tip_if_needed()

    def form_hide(self, **event_args):
        """Clean up when form closes"""
        try:
            if hasattr(window, "stopScanner"):
                window.stopScanner()
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
            Notification("Scanner not ready – JS not loaded.", style="warning", timeout=3).show()

    def button_stop_click(self, **event_args):
        """Stop scanner when button is clicked manually"""
        if hasattr(window, "stopScanner"):
            window.stopScanner()
        else:
            Notification("Stop scanner not available.", style="warning", timeout=3).show()

    def add_part(self, barcode_or_partno):
        value = str(barcode_or_partno).strip()
            
        items = list(self.repeating_panel_1.items or [])
    
        # Call server to resolve the part (or None if not found)
        part_info = anvil.server.call("resolve_part", value)
    
        if not part_info:
            # If not found in database → open mapping form
            from ..MapBarCodePartNo import MapBarCodePartNo
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
            Notification("Please enter a Barcode or Part Number before adding.", style="warning", timeout=3).show()
            return
    
        self.add_part(barcode_or_partno)
        self.txt_BarcodePartNo.text = ""  # clear entry

    def btn_Upload_click(self, **event_args):
        """This method is called when the button is clicked"""
        data = [item for item in self.repeating_panel_1.items]
        if data:
            anvil.server.call("save_stocktake", data)
            Notification("Stocktake saved successfully", style="warning", timeout=3).show()
            self.repeating_panel_1.items = []   # clears repeating panel
            self.txt_BarcodePartNo.text = ""
        else:
            Notification("Sorry, please enter data to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()

    def btn_Export_click(self, **event_args):
        """This method is called when the button is clicked"""
        excel_file = anvil.server.call("export_current_parts_and_partno")
        anvil.media.download(excel_file)
        Notification("Car part details exported successfully.", title="Success", style="success", timeout=3).show()

    def _reset_file_uploader(self):
        """Resets the file uploader using the built-in clear method."""
        self.file_loader_import.clear()
        
    def file_loader_import_change(self, file, **event_args):
        """This method is called when a new file is selected for upload."""
        if file is None:
            return

        # Validate file type
        if not file.name.endswith(".xlsx"):
            alert(
                "Invalid file type. Please upload a valid Excel (.xlsx) file.",
                title="Invalid File",
                large=False
            )
            self._reset_file_uploader()  #  Clear after wrong file type alert is dismissed
            return

        # Confirm before proceeding
        confirmed = confirm(
            f"You are about to import '{file.name}'. "
            "This will update car part details and quantities in the database. "
            "Do you want to proceed?",
            title="Confirm Import",
            buttons=[("Yes, Import", True), ("Cancel", False)]
        )
        if not confirmed:
            self._reset_file_uploader()  # Clear on cancel
            return

        # Show progress notification and keep a reference to dismiss it later
        notification = Notification(
            "Importing data, please wait...",
            title="Processing",
            style="info",
            timeout=None
        )
        notification.show()

        try:
            summary = anvil.server.call(
                "import_counting_stock_quantity", file
            )
            if "skipped" in summary.lower():
                alert(summary, title="Import Completed with Warnings", large=True)
            else:
                alert(summary, title="Import Successful", large=False)
        except Exception as e:
            alert(
                f"An error occurred during import:\n\n{str(e)}",
                title="Import Failed",
                large=True
            )
        finally:
            notification.hide()           # Dismiss notification when processing is done
            self._reset_file_uploader()   # Clear after processing completes
        