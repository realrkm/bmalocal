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
        data_to_save = self.repeating_panel_1.items
    
        # 1. Launch the background task
        self.current_task = anvil.server.call("launch_taxonomy_update", data_to_save)
    
        # 2. Start the timer to check on the task every 1 second (1 second = 1)
        self.timer_1.interval = 1

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)

    def timer_1_tick(self, **event_args):
        """This method is called Every 1 seconds. Does not trigger if interval is 0."""
        
        # Ensure we actually have a task running
        if hasattr(self, 'current_task') and self.current_task is not None:
    
            # We use no_loading_indicator so the screen doesn't flash a spinner every second
            with anvil.server.no_loading_indicator:
    
                # Check if the background task has finished
                if self.current_task.is_completed():
    
                    # 1. Stop the timer immediately so it doesn't keep ticking
                    self.timer_1.interval = 0
    
                    # 2. Try to get the result of the task
                    try:
                        result = self.current_task.get_return_value()
                        # Show success notification
                        Notification(result, title="Task Complete", style="success", timeout=5).show()
    
                    except Exception as e:
                        # If the server code crashed, it throws the error here
                        Notification(f"An error occurred: {str(e)}", title="Task Failed", style="danger").show()
    
                    # 3. Clear the task from memory
                    self.current_task = None
