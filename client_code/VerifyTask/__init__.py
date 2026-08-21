from ._anvil_designer import VerifyTaskTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.js.window import window
import anvil.js
from anvil import BlobMedia
import base64
import time
from .. import ModGetData
from datetime import datetime


class VerifyTask(VerifyTaskTemplate):
    def __init__(self, valueID, **properties):
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        self.cmbJobCardID.items =  ModGetData.getJobCardRef(valueID)
        # Select the first item if available
        if self.cmbJobCardID.items:
            self.cmbJobCardID.selected_value = self.cmbJobCardID.items[0][1]
            # Manually call the change handler
            #self.cmbJobCardID_change()
       

    def Save_click(self, **event_args):
        """Triggered when user clicks 'Save' button in Anvil UI"""
        self.Save.enabled = False #Prevent multiple clicks 
        
        if not self.cmbJobCardID.selected_value['ID']:
            Notification("Sorry, please select job card ref to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.cmbJobCardID.focus()
            self.Save.enabled = True
            return

        if not self.txtRemarks.text:
            Notification("Sorry, please enter remarks to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtRemarks.focus()
            self.Save.enabled = True
            return

        try:
            signature = self.signature_form_1.get_signature_image()
        except ValueError:
            Notification("Signature is required.", style="warning", timeout=3).show()
            self.Save.enabled = True
            return
        
        if not self.cmbWorkflow.selected_value:
            Notification("Sorry, please select workflow status to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.cmbWorkflow.focus()
            self.Save.enabled = True
            return
            
        jobCardID = self.cmbJobCardID.selected_value['ID']
        remarks = self.txtRemarks.text
        createdAt = datetime.now()
        status = self.cmbWorkflow.selected_value
            
        anvil.server.call('saveConfirmationDetails', jobCardID, remarks, signature, createdAt) #Save confirmation details and Update job card to completed
        anvil.server.call_s('updateJobCardStatus', jobCardID, status)
        Notification("Verification saved successfully", style="warning", timeout=3).show()

        # Close Form
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)
        get_open_form().btn_Workflow_click()
