from ._anvil_designer import DefectsFormTemplate
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
from .. import ModNavigation
from ..AddMorePartsInConfirmQuote import AddMorePartsInConfirmQuote
from datetime import datetime


class DefectsForm(DefectsFormTemplate):
    def __init__(self, defects_data=None, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
               
        self.populateForm(defects_data)
        # Store defects_data for later use
        self.defects_data = defects_data
    
        items = anvil.server.call("getStaffAndTechnicianNames")
        # Convert to a list of (display_text, value) tuples
        self.drop_down_staff.items = items
                
    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        

    def populateForm(self, defects_data, **event_args):
        """This method is called when an item is selected""" 
        defectListData=anvil.server.call("getDefectsList", defects_data[0]["ID"])
        #self.txtClientInstructions.text = ModGetData.getJobCardInstructions(defects_data[0]["ID"])
        #self.txtTechNotes.text = ModGetData.getJobCardTechNotes(defects_data[0]["ID"])
        #self.txtDefectsList.text = anvil.server.call('getJobCardDefects',defects_data[0]["ID"])
        #self.txtRequestedParts.text = anvil.server.call('getRequestedParts',defects_data[0]["ID"])
        if defectListData:
            self.txtClientInstructions.text = defectListData[0]['Instruction']
            self.txtTechNotes.text = defectListData[0]['Notes']
            self.txtDefectsList.text = defectListData[0]['Defects']
            self.txtPricedDefectsList.text=defectListData[0]['PricedDefects']
            self.txtTechnicianPortalRequestedParts.text=defectListData[0]["TechnicianPortalRequestedParts"]
            self.txtRequestedParts.text = defectListData[0]['RequestedParts']
            self.drop_down_staff.selected_value = defectListData[0]["PreparedByStaff"]
            self.image_1.source = defectListData[0]["Signature"]

        if not self.txtClientInstructions.text:
            getJobCardDetails = anvil.server.call("getJobCardRow", defects_data[0]["ID"])
            self.txtClientInstructions.text = getJobCardDetails["ClientInstruction"]
            self.txtTechNotes.text = getJobCardDetails["Notes"]
            
        #result = anvil.server.call("getDefectsStaffAndSignature",defects_data[0]["ID"])
        #if result: #Return existing details
        #    self.image_1.source = result[0]["Signature"]

        
    def btn_Update_click(self,  **event_args):
        """This method is called when the button is clicked"""
        self.btn_Update.enabled = False
        jobcardID = self.defects_data[0]["ID"]
        instructions= self.txtClientInstructions.text
        notes = self.txtTechNotes.text
        defects = self.txtDefectsList.text
        priceddefects = self.txtPricedDefectsList.text
        parts=self.txtRequestedParts.text
        staffID = self.drop_down_staff.selected_value
        signature = None
            
        
        if not staffID:
            alert("Sorry, please select staff to proceed", title="Blank Field Found")
            self.drop_down_staff.focus()
            self.btn_Update.enabled = True
            return
            
        if self.label_staffchanged.text == "Yes":
            signature = self.signature_form_1.get_signature_image()
            if not signature:
                self.btn_Update.enabled = True
                return
        
        existingrecord = anvil.server.call("getJobCardDefects", jobcardID)
        if not existingrecord:
            #Create record first in tbl_techniciandefectsandrequestedparts
            anvil.server.call('saveTecnicianDefectsAndRequestedParts', jobcardID, defects, priceddefects, parts, staffID, signature)
            #Transition Checked In jobcards to Create Quote since data now exists in tbl_techniciandefectsandrequestedparts
            anvil.server.call_s("transitionCheckedInToCreateQuote")
            

        anvil.server.call("updateDefectsList", jobcardID, instructions, notes, defects, priceddefects, parts, staffID, signature)
        
        #Update Blank Defects And Requested Parts
        anvil.server.call_s("updateBlankDefectsAndRequestedParts")
        
        alert("Update is successful", title="Success")
        self.column_panel_update_signature.visible=False
        self.populateForm(self.defects_data)
        self.btn_Update.enabled = True
        
    def btn_DownloadTechNotes_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_DownloadTechNotes.enabled=False
        jobcardIDWithTechNotes = anvil.server.call("getTechNotes",self.defects_data[0]["ID"])
        # Normalize the check: strip strings and handle casing
        invalid_values = [None, "", "none", "None"]

        # Check if the value is valid
        # We use .strip() if it's a string to handle whitespace-only entries
        val_to_check = jobcardIDWithTechNotes.strip() if isinstance(jobcardIDWithTechNotes, str) else jobcardIDWithTechNotes

        if val_to_check not in invalid_values:
            # Download Tech Notes
            self.downloadTechNotesPdf(self.defects_data[0]["ID"])
            alert("Tech Notes PDF download is successful", title="Success")
        else:
            alert("Jobcard has no tech notes", title="Missing Tech Notes")
        self.btn_DownloadTechNotes.enabled=True 

    def downloadTechNotesPdf(self, job_card_id):
        result = anvil.server.call("get_tech_notes_details_by_job_id", job_card_id)
        if result is None:
            anvil.alert(
                "No data was returned from the server. Please confirm the tech notes data exists.",
                title="Data Error",
                large=False
            )
        else:
            media_object = anvil.server.call('downloadTechNotesPdfForm', job_card_id, "TechNotes")
            anvil.media.download(media_object)
            self.deleteFile(job_card_id, "TechNotes")


    def btn_DownloadDefectsList_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_DownloadDefectsList.enabled=False
        jobcardID = self.defects_data[0]["ID"]
        self.downloadDefectsPdf(jobcardID)
        self.btn_DownloadDefectsList.enabled=True
              
    def downloadDefectsPdf(self, job_card_id):
        #Check for existing data first
        result = anvil.server.call("get_defects_list_details_by_job_id", job_card_id)
        if result is None:
            anvil.alert(
                "No data was returned from the server. Please confirm the defects data exists.",
                title="Data Error",
                large=False
            )
        else:
            media_object = anvil.server.call('downloadDefectsPdfForm', job_card_id, "DefectsList")
            anvil.media.download(media_object)
            self.deleteFile(job_card_id, "DefectsList")

    def btn_DownloadPricedDefectsList_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_DownloadPricedDefectsList.enabled=False
        jobcardID = self.defects_data[0]["ID"]
        self.downloadPricedDefectsPdf(jobcardID)
        self.btn_DownloadPricedDefectsList.enabled=True
        
    def downloadPricedDefectsPdf(self, job_card_id):
        #Check for existing data first
        result = anvil.server.call("get_priced_defects_list_details_by_job_id", job_card_id)
        if result is None:
            anvil.alert(
                "No data was returned from the server. Please confirm the defects data exists.",
                title="Data Error",
                large=False
            )
        else:
            media_object = anvil.server.call('downloadDefectsPdfForm', job_card_id, "PricedDefectsList")
            anvil.media.download(media_object)
            self.deleteFile(job_card_id, "PricedDefectsList")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

    def drop_down_staff_change(self, **event_args):
        """This method is called when an item is selected"""
        if self.drop_down_staff.selected_value:
            self.label_staffchanged.text = "Yes"
            alert("Update Signature", title="Staff Name Changed")
            self.column_panel_update_signature.visible=True

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

    def drop_down_selectPart_change(self, **event_args):
        """This method is called when an item is selected"""
        self.txtSellingPrice.text = ModGetData.getSellingPrice(self.drop_down_selectPart.selected_value)

    def btn_IssueInvoice_click(self, **event_args):
        """This method is called when the button is clicked"""
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        anvil.server.call("publish_role_notification",self.defects_data[0]["ID"], f"ready for invoicing - {now_str}" )
        alert("Alert has been sent successfully", title="Issue Invoice")


    def btn_IncompleteDefectsInfo_click(self, **event_args):
        """This method is called when the button is clicked"""
        anvil.server.call("publish_defects_notification",self.defects_data[0]["ID"], "defects list incomplete" )
        alert("Incomplete defects list updated ", title="Success")
        

    def btn_AddMorePartsAndServicesInConfirmedQuote_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_AddMorePartsAndServicesInConfirmedQuote.enabled=False
        result = anvil.server.call("getJobCardRow", self.defects_data[0]["ID"])
        if result["Status"] == "In Service" or result["Status"] == "Verify Task" or  result["Status"] == "Issue Invoice":
            alert(content=AddMorePartsInConfirmQuote(self.defects_data[0]["ID"]), buttons=[], dismissible=False,large=True)
            self.btn_AddMorePartsAndServicesInConfirmedQuote.enabled=True
        else:
            alert("Sorry, you can only update In Service, Verify Task or Issue Invoice jobcards.", title="Workflow Action", large=False)
            self.btn_AddMorePartsAndServicesInConfirmedQuote.enabled=True