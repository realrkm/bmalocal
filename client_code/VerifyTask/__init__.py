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
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors) #Set global server error handler
        
        self.cmbJobCardID.items =  ModGetData.getJobCardRef(valueID)
        # ✅ Select the first item if available
        if self.cmbJobCardID.items:
            self.cmbJobCardID.selected_value = self.cmbJobCardID.items[0][1]
            # ✅ Manually call the change handler
            #self.cmbJobCardID_change()
       
    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)   
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def get_signature_image(self):
        # Wait a short time to ensure JS function is available
        for _ in range(20):  # Retry for up to 1 seconds
            if hasattr(window, "getSignatureData"):
                break
            time.sleep(0.5)
        else:
            alert("Signature pad is not ready. Please try again in a moment.")
            return

        # Call the JavaScript function
        data_url = window.getSignatureData()

        if not data_url:
            alert("No signature was captured. Please draw a signature first.")
            return

        # Split data URL to get the base64 content
        header, encoded = data_url.split(",", 1)
        binary_data = base64.b64decode(encoded)

        # Create an Anvil Media object
        media = BlobMedia("image/png", binary_data, name="signature.png")

        # Optionally display it on the form (if you have an Image component)
        #self.signature_preview.source = media

        # Return or store the media for further use
        return media

    def Save_click(self, **event_args):
        """Triggered when user clicks 'Save' button in Anvil UI"""
        self.Save.enabled = False #Prevent multiple clicks 
        
        if not self.cmbJobCardID.selected_value['ID']:
            alert("Sorry, please select job card ref to proceed.", title="Blank Field(s) Found", large=False)
            self.cmbJobCardID.focus()
            self.Save.enabled = True
            return

        if not self.txtRemarks.text:
            alert("Sorry, please enter remarks to proceed.", title="Blank Field(s) Found", large=False)
            self.txtRemarks.focus()
            self.Save.enabled = True
            return
                   
        if not self.get_signature_image():
            self.get_signature_image()
            self.Save.enabled = True
            return
        
        if not self.cmbWorkflow.selected_value:
            alert("Sorry, please select workflow status to proceed.", title="Blank Field(s) Found", large=False)
            self.cmbWorkflow.focus()
            self.Save.enabled = True
            return
            
        jobCardID = self.cmbJobCardID.selected_value['ID']
        remarks = self.txtRemarks.text
        signature = self.get_signature_image()
        createdAt = datetime.now()
        status = self.cmbWorkflow.selected_value
            
        anvil.server.call('saveConfirmationDetails', jobCardID, remarks, signature, createdAt) #Save confirmation details and Update job card to completed
        anvil.server.call_s('updateJobCardStatus', jobCardID, status)
        alert("Verification saved successfully")

        # Close Form
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)
        get_open_form().btn_Workflow_click()
