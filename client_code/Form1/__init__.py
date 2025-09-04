from ._anvil_designer import Form1Template
from anvil.js import window
from anvil import *
import anvil.server

class Form1(Form1Template):
    def __init__(self, **properties):
        self.init_components(**properties)
        # Initialize the label (optional, since HTML handles result display)
       
        # Load the BarcodeScanner HTML into the html_scanner component
       

    def button_scan_click(self, **event_args):
        # Start the scanner (optional, as the HTML has its own start button)
        window.startScanner()
        # Optionally fetch the result from the server
        try:
            result = anvil.server.call('display_result')
            if result:
                code = f"Scan Result: {result}"
                alert(code)
        except Exception as e:
            error = f"Error: {str(e)}"
            alert(error)