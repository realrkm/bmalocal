from ._anvil_designer import DefectsFormTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


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

        items = anvil.server.call_s("getStaff")
        # Convert to a list of (display_text, value) tuples
        self.drop_down_staff.items = [(s['Staff'], s['ID']) for s in items]
        self.signature_component_1.visible = False

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
        self.txtDefectsList.text = anvil.server.call_s('getJobCardDefects',defects_data[0]["ID"])
        self.txtRequestedParts.text = anvil.server.call_s('getRequestedParts',defects_data[0]["ID"])
        result = anvil.server.call("getDefectsStaffAndSignature",defects_data[0]["ID"])
        self.drop_down_staff.selected_value = result[0]["PreparedByStaffID"]
        self.image_1.source = result[0]["Signature"]

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

    def btn_Update_click(self,  **event_args):
        """This method is called when the button is clicked"""
        jobcardID = self.defects_data[0]["ID"]
        instructions= self.txtClientInstructions.text
        notes = self.txtTechNotes.text
        defects = self.txtDefectsList.text
        parts=self.txtRequestedParts.text

        anvil.server.call("updateDefectsList", jobcardID, instructions, notes,defects,parts)
        alert("Update is successfull", title="Success")
        self.btn_Close_click()

    def btn_DownloadDefectsList_click(self, **event_args):
        """This method is called when the button is clicked"""
        jobcardID = self.defects_data[0]["ID"]
        self.downloadQuotationPdf(jobcardID)
              
    def downloadQuotationPdf(self, job_card_id):
        media_object = anvil.server.call('downloadRevisionPdfForm', job_card_id, "DefectsList")
        anvil.media.download(media_object)
        self.deleteFile(job_card_id, "DefectsList")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def btn_UpdateSignature_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.label_signature.visible = False
        self.image_1.visible = False
        self.signature_component_1.visible=True
        self.btn_UpdateSignature.visible = False
