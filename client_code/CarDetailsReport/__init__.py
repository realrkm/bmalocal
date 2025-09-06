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
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.car_repeater.items = anvil.server.call("get_car_details", None)
        set_default_error_handling(
            self.handle_server_errors
        )  # Set global server error handler

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert(
                "Connection to server lost. Please check your internet or try again later.",
                title="Disconnected",
                large=False,
            )
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert(
                "Please connect to the internet to proceed.",
                title="No Internet",
                large=False,
            )
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

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
