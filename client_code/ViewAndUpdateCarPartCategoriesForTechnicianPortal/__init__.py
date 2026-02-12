from ._anvil_designer import ViewAndUpdateCarPartCategoriesForTechnicianPortalTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class ViewAndUpdateCarPartCategoriesForTechnicianPortal(ViewAndUpdateCarPartCategoriesForTechnicianPortalTemplate):
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
        # self.repeating_panel_1.items contains the list of dictionaries
        data_to_save = self.repeating_panel_1.items
    
        # Show a loading notification
        n = Notification("Saving changes...")
        n.show()
    
        # Call the server function
        result = anvil.server.call('update_carpart_taxonomy', data_to_save)

        # Create an instance of the loading spinner and store it in a variable
        self.loading_indicator = anvil.server.loading_indicator()
        
        # Start and stop the indicator however you wish
        self.loading_indicator.start()
        
        # Alert the result (e.g., "Taxonomy updated successfully!")
        alert(result)
        self.loading_indicator.stop()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)
