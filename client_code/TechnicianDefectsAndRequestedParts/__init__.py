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
        self.cmbJobCardRef.items =  ModGetData.getJobCardRef(valueID)
            #  Select the first item if available
        if self.cmbJobCardRef.items:
            self.cmbJobCardRef.selected_value = self.cmbJobCardRef.items[0][1]
            # Manually call the change handler
            self.cmbJobCardRef_change()

        items = anvil.server.call_s("getStaffAndTechnicianNames")
        # Convert to a list of (display_text, value) tuples
        self.drop_down_staff.items =items
                       

    def cmbJobCardRef_change(self, **event_args):
        """This method is called when an item is selected"""
        self.txtClientInstructions.text = ModGetData.getJobCardInstructions(self.cmbJobCardRef.selected_value['ID'])
        self.txtTechNotes.text= ModGetData.getJobCardTechNotes(self.cmbJobCardRef.selected_value['ID'])  

    
        
    def btn_Save_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Save.enabled = False #Prevent multiple clicks

        jobcardref = self.cmbJobCardRef.selected_value['ID']
        defects = self.txtDefectsList.text
        requestedParts = self.txtRequestedParts.text
        status = self.cmbWorkflow.selected_value
        staffID = self.drop_down_staff.selected_value
        
        
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

        try:
            signature = self.signature_form_1.get_signature_image()
        except ValueError:
            alert("Sorry, please sign defects list to proceed.", title="Missing Signature", large=False)
            self.btn_Save.enabled = True
            return   
                        
        
        anvil.server.call('saveTecnicianDefectsAndRequestedParts', jobcardref, defects, defects, requestedParts, staffID, signature)
        anvil.server.call_s('updateJobCardStatus', jobcardref, status)

        if status == "Cancel Jobcard":
            anvil.server.call("saveCancellationReason", jobcardref, self.text_area_1.text)

        #Update Blank Defects And Requested Parts
        anvil.server.call_s("updateBlankDefectsAndRequestedParts")
        
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

    
        

 

   