from ._anvil_designer import Form2Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class Form2(Form2Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        # 1. Load the dictionary from the server
        results = anvil.server.call("load_taxonomy")
        
        # 2. Transform dict {'Category': [patterns]} -> list [{'category': '...', 'patterns': '...'}]
        formatted_items = []
        for category, patterns in results.items():
            # Join the list of patterns into a single string (optional, but good for display)
            patterns_str = ", ".join(patterns)
        
            formatted_items.append({
                'Category': category,
                'Patterns': patterns_str 
            })
        
        # 3. Sort the list alphabetically by category (optional but recommended)
        formatted_items.sort(key=lambda x: x['Category'])
        
        # 4. Assign to the repeating panel
        self.repeating_panel_1.items = formatted_items

    
    def btn_UpdatePartsCategories_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(self.repeating_panel_1.items)
