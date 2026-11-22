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
        self._is_mounted = True
        self.set_event_handler("hide", self.form_hide)
        anvil.js.window.setTimeout(self._load_initial_data, 10)

    def form_hide(self, **event_args):
        self._is_mounted = False

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            rows = anvil.server.call("get_car_details", None)
        if self._is_mounted:
            self.car_repeater.items = rows
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_term = self.txt_Search.text.strip()
        part_name=self.txt_PartName.text.strip()

        # 1. No filters selected
        if not search_term and not part_name:
            Notification("Sorry, please enter keyword, part name or both to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            return
        elif search_term and not part_name:
            cardetails = anvil.server.call('get_car_details', search_term)
        else:
            cardetails = anvil.server.call("get_car_details_and_parts", search_term, part_name)
                       
        
        if cardetails:
            self.car_repeater.items = cardetails
        else:
            Notification("No records found for the entered keyword and or part name.", title="Not Found", style="danger", timeout=3).show()
