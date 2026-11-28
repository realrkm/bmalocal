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
    def __init__(self, jobcard_data=None, prewarm_edit=True, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        self._closed = False
        self._prewarmed_edit_form = None
        self.form_data = jobcard_data
        self.populateForm(jobcard_data)
        self.set_event_handler("show", self._on_form_show)
        if prewarm_edit:
            self._schedule_prewarm_edit_form()

    def _on_form_show(self, **event_args):
        self._schedule_prewarm_edit_form()

    def _is_interim_quote_card(self):
        ref = (self.txt_JobCardRef.text or "")
        return ref.split("-")[-1] == "IQ"

    def _prewarm_edit_form(self):
        if self._closed or self._prewarmed_edit_form is not None or not self.form_data:
            return
        if self._is_interim_quote_card():
            return
        try:
            self._prewarmed_edit_form = EditJobCard(jobcard_data=self.form_data)
            with anvil.server.no_loading_indicator:
                ModGetData.getTechniciansCached()
                ModGetData.getStaffCached()
        except Exception:
            self._prewarmed_edit_form = None

    def _schedule_prewarm_edit_form(self):
        try:
            anvil.js.window.setTimeout(self._prewarm_edit_form, 30)
        except Exception:
            pass
            
    def populateForm(self, jobcard_data, **event_args):
        """This method is called when an item is selected"""
        if "AssignedTechnician" in jobcard_data:
            self.text_box_technician.text = jobcard_data["AssignedTechnician"]
        else:
            self.text_box_technician.text = anvil.server.call_s('getAssignedTechnician', jobcard_data["ID"])
        result = jobcard_data     
        self.txt_JobCardRef.text= result["JobCardRef"]
        self.txtDueDate.date = result["DueDate"]
        self.txtReceivedDate.date = result["ReceivedDate"]
        self.txtExpDate.date = result["ExpDate"]


        #Get staff details
        if "CheckedInByName" in result:
            if result["CheckedInByName"]:
                self.label_checkedInBy.text = result["CheckedInByName"]
        else:
            staff = anvil.server.call_s("get_staff_details", result["CheckedInBy"])
            if staff:
                self.label_checkedInBy.text = staff[0]["Fullname"]
        
        self.chkComp.checked= result["Comprehensive"]
        self.chkTPO.checked=result["ThirdParty"]
        self.chkSpare.checked=result["Spare"]
        self.chkJack.checked=result["Jack"]
        self.chkBrace.checked=result["Brace"]
        self.text_area_other_items.text=result["OtherItems"]
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
      
        if "WorkDone" in result:
            self.text_area_work_done.text = result["WorkDone"]
        else:
            self.text_area_work_done.text = anvil.server.call("getWorkDoneInJobCard", jobcard_data["ID"])
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self._closed = True
        self._prewarmed_edit_form = None
        self.raise_event("x-close-alert", value=False)

    def btn_EditJobCard_click(self, **event_args):
        """Swap in pre-warmed EditJobCard inside the existing modal for instant (<10ms) display."""
        # Restrict Editing Job Cards Created For Interim Quotation
        if self._is_interim_quote_card():  # IQ denotes Interim Quotation
            Notification("Sorry, you cannot edit job card created for an interim quotation", title="Edit Restriction", style="warning", timeout=3).show()
            return

        edit_form = self._prewarmed_edit_form
        self._prewarmed_edit_form = None
        if edit_form is None:
            edit_form = EditJobCard(jobcard_data=self.form_data)

        edit_form.set_event_handler(
            "x-close-alert",
            lambda **e: self.raise_event("x-close-alert", value=e.get("value", False)),
        )
        self.clear()
        self.add_component(edit_form, full_width_row=True)
        try:
            modal_el = anvil.js.window.document.querySelector(".modal.in, .modal.show, .modal")
            if modal_el:
                modal_el.scrollTop = 0
        except Exception:
            pass

    def btn_DownloadTechNotes_click(self, **event_args):
        """This method is called when the button is clicked"""
        # DOWNLOAD TECH NOTES HERE WHEN NO DEFECTS EXIST, WHEN TECH NOTES EXIST AND DEFECTS DON'T
        self.btn_DownloadTechNotes.enabled=False
        jobcardIDWithTechNotes = anvil.server.call("getTechNotes", self.form_data["ID"])
        # Normalize the check: strip strings and handle casing
        invalid_values = [None, "", "none", "None"]
    
        # Check if the value is valid
        # We use .strip() if it's a string to handle whitespace-only entries
        val_to_check = jobcardIDWithTechNotes.strip() if isinstance(jobcardIDWithTechNotes, str) else jobcardIDWithTechNotes
        
        if val_to_check not in invalid_values:
            # Download Tech Notes
            self.downloadTechNotesPdf(self.form_data["ID"])
            Notification("Tech Notes PDF download is successful", title="Success", style="success", timeout=3).show()
        else:
            Notification("Jobcard has no tech notes", title="Missing Tech Notes", style="danger", timeout=3).show()
        self.btn_DownloadTechNotes.enabled=True 

    def downloadTechNotesPdf(self, job_card_id):
        media_object = anvil.server.call('downloadTechNotesPdfForm', job_card_id, "TechNotes")
        anvil.media.download(media_object)
        self.deleteFile(job_card_id, "TechNotes")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)
        
        
