from ._anvil_designer import CarPartsUsedTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class CarPartsUsed(CarPartsUsedTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        #self.repeating_panel_1.items = anvil.server.call('get_car_parts_used', None)
        
    def btn_SearchCustomer_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        if self.txtJobCardRef.text:
            search_value = self.txtJobCardRef.text.strip()
            result = anvil.server.call("getJobCardDetailsWithNameSearch", search_value)
            # Clear drop down
            self.drop_down_JobCardRefDetails.items = ""

            self.drop_down_JobCardRefDetails.items = result
        else:
            alert("Please enter job card ref to proceed.", title="Blank Field(s) Found", large=False)
            self.txtJobCardRef.focus()

    def drop_down_JobCardRefDetails_change(self, **event_args):
        """This method is called when an item is selected"""
        if self.drop_down_JobCardRefDetails.selected_value:
            result = anvil.server.call_s('get_car_parts_used', self.drop_down_JobCardRefDetails.selected_value)
            self.repeating_panel_1.items = result

        else:
            alert("Please enter job card ref to procced.", title="Blank Field(s) Found", large=False)
            self.drop_down_JobCardRefDetails.focus()

    def btn_SearchPart_click(self, **event_args):
        """This method is called when the button is clicked"""
        if self.txtSearchPart.text:
            result = anvil.server.call('get_job_card_from_car_parts_used', self.txtSearchPart.text.strip())
            self.repeating_panel_1.items = result
           
        else:
            alert("Please enter part number to procced.", title="Blank Field(s) Found", large=False)
            self.txtSearchPart.focus()

