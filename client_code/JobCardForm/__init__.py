from ._anvil_designer import JobCardFormTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..EditJobCard import EditJobCard
from .. import ModGetData
import datetime
import anvil.js


class JobCardForm(JobCardFormTemplate):
    def __init__(self, jobcard_data=None, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors)  # Set global server error handler
        self.populateForm(jobcard_data)
        self.form_data = jobcard_data
        
    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert(
                "Connection to server lost. Please check your internet or try again later.",
                title="Disconnected",
                large=False,
            )
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert(
                "Please connect to the internet to proceed.",
                title="No Internet",
                large=False,
            )
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)
            
    def populateForm(self, jobcard_data, **event_args):
        """This method is called when an item is selected"""  
        self.text_box_technician.text = anvil.server.call_s('getAssignedTechnician',jobcard_data["ID"])
        result = jobcard_data     
        self.txt_JobCardRef.text= result["JobCardRef"]
        self.txtDueDate.date = result["DueDate"]
        self.txtReceivedDate.date = result["ReceivedDate"]
        self.txtExpDate.date = result["ExpDate"]


        #Get staff details
        staff= anvil.server.call_s("get_staff_details", result["CheckedInBy"])
        if staff:
            self.label_checkedInBy.text = staff[0]["Fullname"]
        
        self.chkComp.checked= result["Comprehensive"]
        self.chkTPO.checked=result["ThirdParty"]
        self.chkSpare.checked=result["Spare"]
        self.chkJack.checked=result["Jack"]
        self.chkBrace.checked=result["Brace"]
        self.txtRegNo.text=result["RegNo"]
        self.txtMakeAndModel.text=result["MakeAndModel"]
        self.txtChassisNo.text=result["ChassisNo"]
        self.txtEngineCC.text=result["EngineCC"]
        self.txtMileage.text= result["Mileage"]
        self.txtEngineNo.text=result["EngineNo"]
        self.txtEngineCode.text=result["EngineCode"]
        self.txtPaintCode.text=result["PaintCode"]
        self.chkManual.checked=result["Manual"]
        self.chkAuto.checked=result["Auto"]
        self.chkEmpty.checked=result["Empty"]
        self.chkQuarter.checked=result["Quarter"]
        self.chkHalf.checked=result["Half"]
        self.chkThreeQuarter.checked=result["ThreeQuarter"]
        self.chkFull.checked=result["Full"]
        self.txtInstructions.text=result["ClientInstruction"]
        self.txtTechNotes.text=result["Notes"]

        self.text_area_work_done.text = anvil.server.call("getWorkDoneInJobCard", jobcard_data["ID"])
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

    def btn_EditJobCard_click(self, **event_args):
        """This method is called when the button is clicked"""
        
        #Restrict Editing Job Cards Created For Interim Quotation
        #Instead, create a new job card if the custoner wants to fulfil the quote under Workflow cycle.
        if self.txt_JobCardRef.text.split("-")[-1] == "IQ": #IQ denotes Interim Quotation
            alert("Sorry, you cannot edit job card created for an interim quotation",title="Edit Restriction", large=False )
            return
        # This feature is retracted after some customer complained of wrong car details during payment.
        # Hence, allow edits to be made 
        #elif self.form_data["Status"] != "Checked In": #Do not edit job card past Checked In status
        #    alert("Sorry, you can only edit job cards with the 'Checked In' status.",title="Edit Restriction", large=False )
        #    return
        else:
            self.btn_Close_click()
            alert(content=EditJobCard(jobcard_data=self.form_data), buttons=[], dismissible=False,large=True)

    def btn_DownloadTechNotes_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_DownloadTechNotes.enabled=False
        jobcardIDWithTechNotes = anvil.server.call("getTechNotes", self.form_data["ID"])

        if jobcardIDWithTechNotes:
            #Download Tech Notes
            self.downloadTechNotesPdf(self.form_data["ID"])
        else:
            alert("Jobcard has no tech notes", buttons=[], dismissible=False, large=True)
        self.btn_DownloadTechNotes.enabled=True 

    def downloadTechNotesPdf(self, job_card_id):
        media_object = anvil.server.call('downloadTechNotesPdfForm', job_card_id, "TechNotes")
        anvil.media.download(media_object)
        self.deleteFile(job_card_id, "TechNotes")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)
        
        
