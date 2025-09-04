from ._anvil_designer import Form2Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class Form2(Form2Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    
    def display_result(self, result_text):
        """Called from JS when a QR code is scanned"""
        alert(f"Scanned QR Code: {result_text}")
        self.label_result.text = result_text   # Update a label with result

    def button_start_click(self, **event_args):
        """Start scanner from Python when a button is clicked"""
        anvil.js.call_js("startScanner")
    
    def button_stop_click(self, **event_args):
        """Stop scanner from Python when a button is clicked"""
        anvil.js.call_js("stopScanner")