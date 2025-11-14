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
            
        #self.card_1.add_component(DisplayStocktakeAnalysis(None, None, None))
        

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Search.enabled = False   # disable button while searching
        try:
            startDate = self.date_picker_start.date
            endDate = self.date_picker_end.date
            part_no = self.txt_PartNo.text   

            # 1. No filters selected
            if not startDate and not endDate and not part_no:
                alert("Sorry, please select a date range, part number or both to proceed.", 
                      title="Blank Field(s) Found", large=False)
                return

            # 2. Only one date selected
            if (startDate and not endDate) or (endDate and not startDate):
                alert("Please select both start and end dates to proceed.", 
                      title="Missing Date", large=False)
                return

            # 3. Both dates provided but startDate > endDate
            if startDate and endDate and startDate > endDate:
                alert("Sorry, end date should be greater or equal to start date.", 
                      title="Date Mismatch", large=False)
                alert(f"{startDate}")
                alert(f"{endDate}")
                return

            # 4. Fetch based on provided filters
            if startDate and endDate and not part_no:
                alert(content=DisplayStocktakeAnalysis(start_date = startDate, end_date = endDate, partnumber = None),dismissible=False, large=True )
                #self.card_1.clear()
                #self.card_1.add_component()
               
            elif not startDate and not endDate and part_no:
                alert(content=DisplayStocktakeAnalysis(start_date = None, end_date = None, partnumber = part_no),dismissible=False, large=True) 
                #self.card_1.clear()
                #self.card_1.add_component(DisplayStocktakeAnalysis(start_date = None, end_date = None, partnumber = part_no))
                
            elif startDate and endDate and part_no:
                alert(content=DisplayStocktakeAnalysis(start_date =  startDate, end_date = endDate, partnumber = part_no),dismissible=False, large=True)
               # self.card_1.clear()
               # self.card_1.add_component(DisplayStocktakeAnalysis(start_date =  startDate, end_date = endDate, partnumber = part_no))

        finally:
            self.btn_Search.enabled = True   # re-enable button after processing

   