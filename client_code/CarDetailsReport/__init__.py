from ._anvil_designer import CarDetailsReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class CarDetailsReport(CarDetailsReportTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        self.car_repeater.items = anvil.server.call("get_car_details", None)
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_term = self.txt_Search.text.strip()
        part_name=self.txt_PartName.text.strip()

        # 1. No filters selected
        if not search_term and not part_name:
            alert("Sorry, please enter keyword, part name or both to proceed.", title="Blank Field(s) Found", large=False)
            return
        elif search_term and not part_name:
            cardetails = anvil.server.call('get_car_details', search_term)
        else:
            cardetails = anvil.server.call("get_car_details_and_parts", search_term, part_name)
                       
        
        if cardetails:
            self.car_repeater.items = cardetails
        else:
            alert("No records found for the entered keyword and or part name.", title="Not Found", large=False)
