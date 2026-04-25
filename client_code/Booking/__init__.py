from ._anvil_designer import BookingTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class Booking(BookingTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')#Set focus into technician
        self.repeating_panel_1.items = anvil.server.call("getBookingDetails")
        
    def btn_SearchCustomer_click(self, **event_args):
        """This method is called when the button is clicked"""
        valueCustomer = self.txt_ClientName.text
        if valueCustomer is None:
            alert("Enter Customer's name to proceed", title="Blank Field Found")
            return
        else:
            result = anvil.server.call("getClientFullnameFromSearchWord", valueCustomer)
            self.drop_down_selectCustomer.items = result

    def drop_down_selectCustomer_change(self, **event_args):
        """This method is called when an item is selected"""
        # Fetch the list from the server
        reg_numbers = anvil.server.call('getCarRegNoFromClientID', self.drop_down_selectCustomer.selected_value)
    
        # Set the items of your car registration dropdown
        self.drop_down_car_reg.items = reg_numbers

    
    def btn_Save_click(self, **event_args):
        """This method is called when the button is clicked"""
        customer = self.drop_down_selectCustomer.selected_value
        regno = self.drop_down_car_reg.selected_value
        period = self.date_picker_period.date
        details = self.txt_area_details.text
    
        # Check if ANY of the fields are missing (using 'or')
        if not (customer and regno and period and details):
            alert(
                content="Please ensure all fields (Customer, Reg No, Date/Time, and Details) are filled in to proceed.",
                title="Missing Information",
                buttons=[("OK", None)],
                dismissible=True
            )
        else:
            # Call the server to save
            anvil.server.call("saveBookingDetails", customer, regno, period, details)
    
            # Optional: Show success message and clear fields
            alert("Booking saved successfully!")
            self.repeating_panel_1.items = anvil.server.call("getBookingDetails")
            self.clear_form()

    def clear_form(self):
        # It's good practice to reset the UI after a successful save
        self.txt_ClientName.text=""
        self.drop_down_selectCustomer.items = None
        self.drop_down_car_reg.items = None
        self.date_picker_period.date = None
        self.txt_area_details.text = ""
    