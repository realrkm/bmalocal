from ._anvil_designer import InventoryReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..PriceCatalogue import PriceCatalogue
from ..StockLocation import StockLocation
from ..StockBalance import StockBalance
from ..CarPartsUsed import CarPartsUsed
from ..StocktakeAnalysis import StocktakeAnalysis
import anvil.js

class InventoryReport(InventoryReportTemplate):
    def __init__(self, buttonName, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.show_clicked_button(buttonName)

    # This function is called when Contact form loads or when Save And New button is clicked in the forms loaded in card_2 component
    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "Catalogue":
            self.btn_PriceCatalogue_click()
        elif buttonName == "Location":
            self.btn_Location_click()
        elif buttonName == "Balance":
            self.btn_StockBalance_click()
        elif buttonName == "CarParts":
            self.btn_CarPartsUsed_click()

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

    def btn_PriceCatalogue_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("PRICE CATALOGUE")
        self.card_2.clear()
        self.card_2.add_component(PriceCatalogue())
        self.btn_PriceCatalogue.background = "#000000"

    def btn_Location_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("STOCK LOCATION")
        self.card_2.clear()
        self.card_2.add_component(StockLocation())
        self.btn_Location.background = "#000000"

    def btn_StockBalance_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("STOCK BALANCE")
        self.card_2.clear()
        self.card_2.add_component(StockBalance())
        self.btn_StockBalance.background = "#000000"

    def btn_StocktakeAnalysis_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("STOCK ANALYSIS")
        self.card_2.clear()
        self.card_2.add_component(StocktakeAnalysis())
        self.btn_StocktakeAnalysis.background = "#000000"

    def btn_CarPartsUsed_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("CAR PARTS USED")
        self.card_2.clear()
        self.card_2.add_component(CarPartsUsed())
        self.btn_CarPartsUsed.background = "#000000"

    