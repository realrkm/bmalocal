from ._anvil_designer import RowTemplateTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class RowTemplate(RowTemplateTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        # Any code you write here will run before the form opens.
        # Split Part_No and create links
        part_numbers = self.item['Part_No'].split(" / ")
    
        for part in part_numbers:
            l = Link(text=part)
            l.icon = "fa:times"
            l.icon_align = "left"
            l.background = "#eee"
            l.role = "flowPanelLinks"
            l.border = "1px solid #888"
            l.set_event_handler("click", self.remove_part)
            self.flow_panel_partNo.add_component(l)
            
    def remove_part(self, **event_args):
        event_args['sender'].remove_from_parent()
        
    def btn_DeleteRow_click(self, **event_args):
        """This method is called when the button is clicked"""
        items = list(self.parent.items)
        del items[list(self.parent.items).index(self.item)]
        self.parent.items = items

    