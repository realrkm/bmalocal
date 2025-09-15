from ._anvil_designer import StocktakeAnalysisTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..DisplayStocktakeAnalysis import DisplayStocktakeAnalysis
import anvil.js


class StocktakeAnalysis(StocktakeAnalysisTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call("replaceBanner")
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.card_1.clear()
        self.card_1.add_component(DisplayStocktakeAnalysis())

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
