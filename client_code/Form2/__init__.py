from ._anvil_designer import Form2Template
from anvil import *
from anvil.js import window, report_exceptions

class Form2(Form2Template):
    def __init__(self, **properties):
        self.init_components(**properties)

        @report_exceptions
        def _display_result_from_js(result_text):
            alert(f"Scanned QR Code: {result_text}")
            self.label_result.text = result_text

        # Expose callback for JS to call
        window.display_result = _display_result_from_js
        self._js_display_ref = _display_result_from_js

    def form_hide(self, **event_args):
        try:
            window.display_result = None
        except Exception:
            pass

    def button_start_click(self, **event_args):
        window.startScanner()

    def button_stop_click(self, **event_args):
        window.stopScanner()
