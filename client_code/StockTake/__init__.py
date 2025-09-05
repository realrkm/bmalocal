from ._anvil_designer import StockTakeTemplate
from anvil import *
from anvil.js import window, report_exceptions

class StockTake(StockTakeTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)

        # Wrap callback so errors show in Anvil logs
        @report_exceptions
        def _display_result_from_js(result_text):
            # Show result directly in label_result
            self.label_result.text = result_text

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
        self.label_result.text = ""
       
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
