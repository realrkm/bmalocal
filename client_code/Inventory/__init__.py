from ._anvil_designer import InventoryTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js


class Inventory(InventoryTemplate):
    def __init__(self, permissions, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        
        self.permissions = permissions
        self._initial_subform_loaded = False
        self._first_visible = None

        # Apply permissions to buttons
        self.apply_permissions()

        # Defer loading the subform until after the form is attached
        self.set_event_handler("show", self.form_show)

    def form_show(self, **event_args):
        """Loads the first authorized subform once the main Inventory container is mounted."""
        if not self._initial_subform_loaded:
            self._initial_subform_loaded = True
            if self._first_visible:
                self.show_clicked_button(self._first_visible)

    def apply_permissions(self):
        """Apply only INVENTORY-related permissions and record the first available subform."""
        inventory_perms = self.permissions.get("INVENTORY", {"main": False, "subs": {}})

        for subsection, value in inventory_perms["subs"].items():
            if subsection == "Add New Parts":
                self.btn_AddNewParts.visible = value
                self.btn_AddNewParts.enabled = value
                if value and self._first_visible is None:
                    self._first_visible = "AddNewParts"

            elif subsection == "Add More Stock":
                self.btn_AddMoreStock.visible = value
                self.btn_AddMoreStock.enabled = value
                if value and self._first_visible is None:
                    self._first_visible = "AddMoreStock"

            elif subsection == "Stock Taking":
                self.btn_StockTaking.visible = value
                self.btn_StockTaking.enabled = value
                if value and self._first_visible is None:
                    self._first_visible = "StockTaking"

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
        from ..AddNewParts import AddNewParts
        self.highlight_active_button("ADD NEW PARTS")
        self.card_2.clear()
        self.card_2.add_component(AddNewParts())
        self.btn_AddNewParts.background = "#000000"

    def btn_AddMoreStock_click(self, **event_args):
        """This method is called when the button is clicked"""
        from ..AddMoreStock import AddMoreStock
        self.highlight_active_button("ADD MORE STOCK")
        self.card_2.clear()
        self.card_2.add_component(AddMoreStock(), full_width_row=True)
        self.btn_AddMoreStock.background = "#000000"

    def btn_StockTaking_click(self, **event_args):
        """This method is called when the button is clicked"""
        from ..StockTake import StockTake
        self.highlight_active_button("STOCK TAKE")
        self.card_2.clear()
        self.card_2.add_component(StockTake(), full_width_row=True)
        self.btn_StockTaking.background = "#000000"
