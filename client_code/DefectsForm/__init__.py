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
from datetime import datetime


class DefectsForm(DefectsFormTemplate):
    def __init__(self, defects_data=None, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors)  # Set global server error handler

        self.populateForm(defects_data)
        # Store defects_data for later use
        self.defects_data = defects_data

        items = anvil.server.call("getStaff")
        # Convert to a list of (display_text, value) tuples
        self.drop_down_staff.items = [(s['Staff'], s['ID']) for s in items]

        #Store JobcardID 
        self.jobcardid = defects_data[0]["ID"]
         
    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.",title="Disconnected",large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.",title="No Internet",large=False)
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def populateForm(self, defects_data, **event_args):
        """This method is called when an item is selected"""   
        self.txtClientInstructions.text = ModGetData.getJobCardInstructions(defects_data[0]["ID"])
        self.txtTechNotes.text = ModGetData.getJobCardTechNotes(defects_data[0]["ID"])
        self.txtDefectsList.text = anvil.server.call('getJobCardDefects',defects_data[0]["ID"])
        self.txtRequestedParts.text = anvil.server.call('getRequestedParts',defects_data[0]["ID"])
        result = anvil.server.call("getDefectsStaffAndSignature",defects_data[0]["ID"])
        if result: #Return existing details
            self.drop_down_staff.selected_value = result[0]["PreparedByStaffID"]
            self.image_1.source = result[0]["Signature"]

    
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
        
    def btn_Update_click(self,  **event_args):
        """This method is called when the button is clicked"""
        self.btn_Update.enabled = False
        jobcardID = self.defects_data[0]["ID"]
        instructions= self.txtClientInstructions.text
        notes = self.txtTechNotes.text
        defects = self.txtDefectsList.text
        parts=self.txtRequestedParts.text
        staffID = self.drop_down_staff.selected_value
        signature = None
        
        if not staffID:
            alert("Sorry, please select staff to proceed", title="Blank Field Found")
            self.drop_down_staff.focus()
            self.btn_Update.enabled = True
            return
            
        if self.label_staffchanged.text == "Yes":
            signature = self.get_signature_image()
            if not signature:
                self.btn_Update.enabled = True
                return
            
        anvil.server.call("updateDefectsList", jobcardID, instructions, notes,defects,parts, staffID, signature)
        alert("Update is successful", title="Success")
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
        media_object = anvil.server.call('downloadTechNotesPdfForm', job_card_id, "TechNotes")
        anvil.media.download(media_object)
        self.deleteFile(job_card_id, "TechNotes")


    def btn_DownloadDefectsList_click(self, **event_args):
        """This method is called when the button is clicked"""
        jobcardID = self.defects_data[0]["ID"]
        self.downloadDefectsPdf(jobcardID)
              
    def downloadDefectsPdf(self, job_card_id):
        media_object = anvil.server.call('downloadDefectsPdfForm', job_card_id, "DefectsList")
        anvil.media.download(media_object)
        self.deleteFile(job_card_id, "DefectsList")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

    def drop_down_staff_change(self, **event_args):
        """This method is called when an item is selected"""
        if self.drop_down_staff.selected_value > 0:
            self.label_staffchanged.text = "Yes"
            alert("Update Signature", title="Staff Name Changed")

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
        anvil.server.call("publish_role_notification",self.jobcardid, f"ready for invoicing - {now_str}" )
        ModNavigation.go_Notification()
        alert("Alert has been sent successfully", title="Issue Invoice")


    def btn_IncompleteDefectsInfo_click(self, **event_args):
        """This method is called when the button is clicked"""
        anvil.server.call("publish_defects_notification",self.jobcardid, "defects list incomplete" )
        alert("Incomplete defects list updated ", title="Success")
        ModNavigation.go_Enable_Incomplete_Defects_Info()
    