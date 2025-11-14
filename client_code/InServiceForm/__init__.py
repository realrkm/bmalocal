from ._anvil_designer import InServiceFormTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.media
import anvil.js
from .. import ModGetData
from ..EditQuote import EditQuote
from datetime import date

class InServiceForm(InServiceFormTemplate):
    def __init__(self, valueID, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors) #Set global server error handler
        
        self.cmbJobCardRef.items =  ModGetData.getJobCardRef(valueID)
        # ✅ Select the first item if available
        if self.cmbJobCardRef.items:
            self.cmbJobCardRef.selected_value = self.cmbJobCardRef.items[0][1]
            # ✅ Manually call the change handler
            self.cmbJobCardRef_change()
            
    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)   
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    
    def cmbJobCardRef_change(self, **event_args):
        """This method is called when an item is selected"""
        self.txtClientInstructions.text = ModGetData.getJobCardInstructions(self.cmbJobCardRef.selected_value['ID'])
        self.text_box_technician.text = ModGetData.getAssignedTechnician(self.cmbJobCardRef.selected_value['ID'])
        self.txtTechNotes.text= ModGetData.getJobCardTechNotes(self.cmbJobCardRef.selected_value['ID'])
        self.txtDefectsList.text = ModGetData.getJobCardDefects(self.cmbJobCardRef.selected_value['ID'])
        self.txtRequestedParts.text = ModGetData.getRequestedParts(self.cmbJobCardRef.selected_value['ID'])
        self.repeating_panel_1.items = ModGetData.getClientQuotationFeedback(self.cmbJobCardRef.selected_value['ID'])

    def btn_Save_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Save.enabled = False #Prevent multiple clicks
        
        if not self.cmbWorkflow.selected_value:
            alert("Sorry, please select the next workflow status to proceed.", title="Blank Field(s) Found")
            self.cmbWorkflow.focus()
            self.btn_Save.enabled = True
            return
            
        if not self.text_area_work_done.text:
            alert("Sorry, please enter the work done to proceed.", title="Blank Field(s) Found")
            self.text_area_work_done.focus()
            self.btn_Save.enabled = True
            return
            
        jobCardID = self.cmbJobCardRef.selected_value['ID']
        status = self.cmbWorkflow.selected_value  
        workDone = self.text_area_work_done.text
        anvil.server.call_s('updateJobCardStatus', jobCardID, status)
        anvil.server.call("saveWorkDoneInJobCard", jobCardID, workDone)
        alert("Service saved successfully", title="Success")
        # Close Form
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)
        get_open_form().btn_Workflow_click()
