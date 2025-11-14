from ._anvil_designer import TransitionInterimQuoteToInvoiceTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class TransitionInterimQuoteToInvoice(TransitionInterimQuoteToInvoiceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def btn_Search_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        if self.txtJobCardRef.text:
            search_value = self.txtJobCardRef.text.strip()
            result = anvil.server.call("getInterimQuote", search_value)
            # Clear drop down
            self.drop_down_JobCardRefDetails.items = ""

            self.drop_down_JobCardRefDetails.items = result
        else:
            alert("Please enter job card ref to proceed.", title="Blank Field(s) Found", large=False)
            self.txtJobCardRef.focus()

    def btn_Transition_click(self, **event_args):
        """This method is called when the button is clicked"""
        if self.drop_down_JobCardRefDetails.selected_value:
            anvil.server.call("transitionInterimQuoteToInvoice", self.drop_down_JobCardRefDetails.selected_value)
            alert("Interim Quote Transitioned To Invoice", title="Success")
            #Close Form
            self.btn_Close_click()
        else:
            alert("Sorry, please select the jobcard ref to proceed", title="Blank Foeld(s) Found")

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
            
            
