from ._anvil_designer import AddMoreStockTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from ..EditClient import EditClient
from .. import ModNavigation
import re


class AddMoreStock(AddMoreStockTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()

        set_default_error_handling(
            self.handle_server_errors
        )  # Set global server error handler

        self.drop_down_selectSupplier.items = anvil.server.call("getSupplier")
        
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

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_Search_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        search_value = self.text_box_searchPartNo.text.strip()

        if not search_value:
            alert("Please enter part name or part no. to proceed.", title="Blank Field(s) Found", large=False)
            self.text_box_searchPartNo.focus()
            return

        result = anvil.server.call('getCarPartNameAndNumber', search_value)

        #Clear drop down 
        self.drop_down_selectPart.items = ""

        if result:
            self.drop_down_selectPart.items = result
        else:
            alert("No records found for the entered part detail.", title="Not Found")


    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_SaveAndNew.enabled = False  # Disable button to prevent multiple clicks

        additionDate = self.date_picker_1.date
        supplier = self.drop_down_selectSupplier.selected_value
        partID = self.drop_down_selectPart.selected_value
        no_of_units = self.txt_NoOfUnits.text
        unit_cost = self.txt_UnitCost.text

        if not additionDate:
            alert("Please enter date to proceed.")
            self.additionDate.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not supplier:
            alert("Please select supplier to proceed.")
            self.drop_down_selectSupplier.focus()
            self.btn_SaveAndNew.enabled = True
            return
            
        if not no_of_units:
            alert("Please enter number of units to proceed.")
            self.txt_NoOfUnits.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not unit_cost:
            alert("Please enter unit cost to proceed.")
            self.txt_UnitCost.focus()
            self.btn_SaveAndNew.enabled = True
            return

        # Save data
        anvil.server.call("addStock", additionDate, supplier, partID,  no_of_units, unit_cost)
        alert("Stock added successfully.")

        # Clear form
        self.clear_form_fields()

    def drop_down_selectPart_change(self, **event_args):
        """This method is called when an item is selected"""
        search_text = self.drop_down_selectPart.selected_value
        result = anvil.server.call("get_buying_prices_by_partID", search_text)

        if result:
            # Clear drop down
            self.repeating_panel_1.items = ""
            self.repeating_panel_1.items = result
        else:
            alert("No records found for the entered part detail.", title="Not Found")

    def clear_form_fields(self):
        """Reset all fields after saving"""
        self.date_picker_1.date = None
        self.drop_down_selectSupplier.items =[]
        self.text_box_searchPartNo.text = ""
        self.drop_down_selectPart.items = []
        self.drop_down_selectPart.selected_value = None
        self.txt_NoOfUnits.text = ""
        self.txt_UnitCost.text = ""
        self.repeating_panel_1.items = []
        self.drop_down_selectSupplier.items = anvil.server.call("getSupplier")
        # Put cursor back on search box for next entry
        self.text_box_searchPartNo.focus()
        
        self.refresh()
        self.btn_SaveAndNew.enabled =True

   