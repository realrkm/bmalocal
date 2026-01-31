from ._anvil_designer import TechnicianDefectsAndRequestedPartsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.js.window import window
import anvil.js
import base64
import time
from .. import ModGetData

class TechnicianDefectsAndRequestedParts(TechnicianDefectsAndRequestedPartsTemplate):
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

        items = anvil.server.call_s("getStaff")
        # Convert to a list of (display_text, value) tuples
        self.drop_down_staff.items = [(s['Staff'], s['ID']) for s in items]
        
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
        self.txtTechNotes.text= ModGetData.getJobCardTechNotes(self.cmbJobCardRef.selected_value['ID'])  

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

        # Return or store the media for further use
        return media
        
    def btn_Save_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Save.enabled = False #Prevent multiple clicks

        jobcardref = self.cmbJobCardRef.selected_value['ID']
        defects = self.txtDefectsList.text
        requestedParts = self.txtRequestedParts.text
        status = self.cmbWorkflow.selected_value
        staffID = self.drop_down_staff.selected_value
        signature = self.get_signature_image()
        
        if not self.cmbJobCardRef.selected_value:
            alert("Sorry, please select job card ref to proceed.", title="Blank Field(s) Found")
            self.cmbJobCardRef.focus()
            self.btn_Save.enabled = True
            return

        if not self.txtDefectsList.text:
            defects="None"
            
        if not self.txtRequestedParts.text:
            requestedParts="None"
            
        if not self.cmbWorkflow.selected_value:
            alert("Sorry, please select workflow status to proceed.", title="Blank Field Found")
            self.cmbWorkflow.focus()
            self.btn_Save.enabled = True
            return
            
        if self.cmbWorkflow.selected_value == "Cancel Jobcard" and not self.text_area_1.text:
            alert("Sorry, please enter cancellation reason to proceed.", title="Blank Field Found")
            self.text_area_1.focus()
            self.btn_Save.enabled = True
            return
            
        if not self.drop_down_staff.selected_value:
            alert("Sorry, please select staff who prepared the defects list.", title="Blank Field Found")
            self.drop_down_staff.focus()
            self.btn_Save.enabled = True
            return
            
        if not self.get_signature_image():
            self.btn_Save.enabled = True
            return   
        
        anvil.server.call('saveTecnicianDefectsAndRequestedParts', jobcardref, defects, requestedParts, staffID, signature)
        anvil.server.call_s('updateJobCardStatus', jobcardref, status)

        if status == "Cancel Jobcard":
            anvil.server.call("saveCancellationReason", jobcardref, self.text_area_1.text)
        
        alert("Data saved successfully", title="Success")
            
        # Close Form 
        self.btn_Close_click()
    
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)
        get_open_form().btn_Workflow_click()

    def cmbWorkflow_change(self, **event_args):
        """This method is called when an item is selected"""
        if self.cmbWorkflow.selected_value == "Cancel Jobcard":
            self.text_area_1.visible=True
        else:
            self.text_area_1.visible = False
        

 

   