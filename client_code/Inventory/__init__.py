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
import anvil.js


class Inventory(InventoryTemplate):
    def __init__(self, permissions, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.permissions = permissions

        # Apply permissions to buttons and load the first available subform
        self.apply_permissions()

    def apply_permissions(self):
        """Apply only INVENTORY-related permissions and load the first available subform."""
        inventory_perms = self.permissions.get("INVENTORY", {"main": False, "subs": {}})

        first_visible = None  # track which subform to load first

        for subsection, value in inventory_perms["subs"].items():
            if subsection == "Add New Parts":
                self.btn_AddNewParts.visible = value
                self.btn_AddNewParts.enabled = value
                if value and first_visible is None:
                    first_visible = "AddNewParts"

            elif subsection == "Add More Stock":
                self.btn_AddMoreStock.visible = value
                self.btn_AddMoreStock.enabled = value
                if value and first_visible is None:
                    first_visible = "AddMoreStock"

            elif subsection == "Stock Taking":
                self.btn_StockTaking.visible = value
                self.btn_StockTaking.enabled = value
                if value and first_visible is None:
                    first_visible = "StockTaking"

        # Load the first visible subform automatically
        if first_visible:
            self.show_clicked_button(first_visible)

    # This function is called when Contact form loads or when Save And New button is clicked in the forms loaded in card_2 component
    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "AddNewParts":
            self.btn_AddNewParts_click()
        elif buttonName == "AddMoreStock":
            self.btn_AddMoreStock_click()
        elif buttonName == "StockTaking":
            self.btn_StockTaking_click()
       
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

    def btn_StockTaking_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("STOCK TAKE")
        self.card_2.clear()
        self.card_2.add_component(StockTake())
        self.btn_StockTaking.background = "#000000"

    