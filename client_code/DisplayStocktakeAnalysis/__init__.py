from ._anvil_designer import DisplayStocktakeAnalysisTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class DisplayStocktakeAnalysis(DisplayStocktakeAnalysisTemplate):
    def __init__(self, start_date=None, end_date=None, partnumber=None,**properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call("replaceBanner")
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.html = anvil.server.call("get_stock_analysis_report",start_date=start_date, end_date=end_date, partnumber=partnumber)
