from ._anvil_designer import InventoryTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..AddNewParts import AddNewParts
from ..AddMoreStock import AddMoreStock
from ..StockTake import StockTake

class Inventory(InventoryTemplate):
    def __init__(self, buttonName, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        self.show_clicked_button(buttonName)

    # This function is called when Contact form loads or when Save And New button is clicked in the forms loaded in card_2 component
    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "AddNewParts":
            self.btn_AddNewParts_click()
        elif buttonName == "AddMoreStock":
            self.btn_AddMoreStock_click()
       
    def highlight_active_button(self, selected_text):
        # Loop through all buttons in the panel
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"  # Highlighted black
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"  # Normal blue
                    comp.foreground = "white"

    def btn_AddNewParts_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("ADD NEW PARTS")
        self.card_2.clear()
        self.card_2.add_component(AddNewParts())
        self.btn_AddNewParts.background = "#000000"

    def btn_AddMoreStock_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("ADD MORE STOCK")
        self.card_2.clear()
        self.card_2.add_component(AddMoreStock())
        self.btn_AddMoreStock.background = "#000000"

    def btn_StockTake_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("STOCK TAKE")
        self.card_2.clear()
        self.card_2.add_component(StockTake())
        self.btn_StockTake.background = "#000000"

  