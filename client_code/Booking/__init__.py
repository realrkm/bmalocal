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

        # External JS call for styling/layout
        anvil.js.call('replaceBanner')

        # Load initial data into the Repeating Panel
        self.refresh_data_grid()

    def refresh_data_grid(self):
        """Helper method to reload the history table"""
        self.repeating_panel_1.items = anvil.server.call("getBookingDetails")

    def btn_SearchCustomer_click(self, **event_args):
        """Search for customers based on the text input"""
        valueCustomer = self.txt_ClientName.text

        # strip() handles cases where the user just enters spaces
        if not valueCustomer or not valueCustomer.strip():
            alert("Enter Customer's name to proceed", title="Blank Field Found")
            return

        result = anvil.server.call("getClientFullnameFromSearchWord", valueCustomer)

        if result:
            self.drop_down_selectCustomer.items = result
        else:
            self.drop_down_selectCustomer.items = []
            Notification("No customers found matching that name.", style="warning").show()

    def drop_down_selectCustomer_change(self, **event_args):
        """Fetch vehicle registrations when a customer is selected"""
        selected_id = self.drop_down_selectCustomer.selected_value
        if selected_id:
            reg_numbers = anvil.server.call('getCarRegNoFromClientID', selected_id)
            self.drop_down_car_reg.items = reg_numbers
        else:
            self.drop_down_car_reg.items = []

    def btn_Save_click(self, **event_args):
        """Validate and save the booking"""
        customer = self.drop_down_selectCustomer.selected_value
        regno = self.drop_down_car_reg.selected_value
        period = self.date_picker_period.date
        details = self.txt_area_details.text

        if not (customer and regno and period and details):
            alert(
                content="Please ensure all fields (Customer, Reg No, Date/Time, and Details) are filled in to proceed.",
                title="Missing Information",
                buttons=[("OK", None)]
            )
        else:
            # Save to DB
            anvil.server.call("saveBookingDetails", customer, regno, period, details)

            # UI Feedback
            Notification("Booking saved successfully!", style="success").show()

            # Refresh the list and clear form
            self.refresh_data_grid()
            self.clear_form()

    def clear_form(self):
        """Reset all input components to their default state"""
        self.txt_ClientName.text = ""
        self.drop_down_selectCustomer.items = []
        self.drop_down_car_reg.items = []
        self.date_picker_period.date = None
        self.txt_area_details.text = ""