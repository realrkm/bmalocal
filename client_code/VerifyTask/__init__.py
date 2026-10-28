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
        self.cmbJobCardID.items = ModGetData.getJobCardRef(valueID)
        # Select the first item if available
        if self.cmbJobCardID.items:
            self.cmbJobCardID.selected_value = self.cmbJobCardID.items[0][1]
            self.load_existing_verify_checklist(self.cmbJobCardID.selected_value['ID'])

    def load_existing_verify_checklist(self, jobCardID):
        """Populate VerifyTask controls if Final Quality & Handover data already exists."""
        try:
            data = anvil.server.call_s('getVerifyTaskChecklist', jobCardID)
        except Exception:
            data = None
        if not data or not isinstance(data, dict):
            return

        self.chk_torque.checked = bool(data.get("chk_torque", False))
        self.chk_test.checked = bool(data.get("chk_test", False))
        self.chk_clean.checked = bool(data.get("chk_clean", False))
        self.chk_old.checked = bool(data.get("chk_old", False))
        self.chk_explain.checked = bool(data.get("chk_explain", False))

        if data.get("next_service_date"):
            try:
                self.date_picker_next_service.date = datetime.strptime(
                    data["next_service_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        self.txt_next_service_mileage.text = (
            str(data["next_service_mileage"])
            if data.get("next_service_mileage") is not None
            else ""
        )

        if data.get("time_start"):
            try:
                self.date_picker_time_start.date = datetime.fromisoformat(data["time_start"])
            except ValueError:
                pass

        if data.get("time_end"):
            try:
                self.date_picker_time_end.date = datetime.fromisoformat(data["time_end"])
            except ValueError:
                pass

        self.txt_efficiency.text = data.get("efficiency") or ""

    def Save_click(self, **event_args):
        """Triggered when user clicks 'Save' button in Anvil UI"""
        self.Save.enabled = False  # Prevent multiple clicks

        if not self.cmbJobCardID.selected_value['ID']:
            Notification("Sorry, please select job card ref to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.cmbJobCardID.focus()
            self.Save.enabled = True
            return

        # Mandatory Final Quality & Handover checkboxes check
        if not all([
            self.chk_torque.checked,
            self.chk_test.checked,
            self.chk_clean.checked,
            self.chk_old.checked,
            self.chk_explain.checked,
        ]):
            Notification(
                "All Final Quality and Handover checkboxes must be ticked before saving.",
                title="Incomplete Checklist",
                style="warning",
                timeout=3
            ).show()
            self.Save.enabled = True
            return

        if not self.date_picker_next_service.date:
            Notification(
                "Sorry, please select the Next Service Date to proceed.",
                title="Blank Field(s) Found",
                style="warning",
                timeout=3
            ).show()
            self.date_picker_next_service.focus()
            self.Save.enabled = True
            return

        if self.txt_next_service_mileage.text in (None, ""):
            Notification(
                "Sorry, please enter the Next Service Mileage to proceed.",
                title="Blank Field(s) Found",
                style="warning",
                timeout=3
            ).show()
            self.txt_next_service_mileage.focus()
            self.Save.enabled = True
            return

        if not self.date_picker_time_start.date:
            Notification(
                "Sorry, please select Time started to proceed.",
                title="Blank Field(s) Found",
                style="warning",
                timeout=3
            ).show()
            self.date_picker_time_start.focus()
            self.Save.enabled = True
            return

        if not self.date_picker_time_end.date:
            Notification(
                "Sorry, please select Time finished to proceed.",
                title="Blank Field(s) Found",
                style="warning",
                timeout=3
            ).show()
            self.date_picker_time_end.focus()
            self.Save.enabled = True
            return

        if not (self.txt_efficiency.text or "").strip():
            Notification(
                "Sorry, please enter Efficiency to proceed.",
                title="Blank Field(s) Found",
                style="warning",
                timeout=3
            ).show()
            self.txt_efficiency.focus()
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

        verify_checklist_data = {
            "chk_torque": bool(self.chk_torque.checked),
            "chk_test": bool(self.chk_test.checked),
            "chk_clean": bool(self.chk_clean.checked),
            "chk_old": bool(self.chk_old.checked),
            "chk_explain": bool(self.chk_explain.checked),
            "next_service_date": (
                self.date_picker_next_service.date.strftime("%Y-%m-%d")
                if self.date_picker_next_service.date else None
            ),
            "next_service_mileage": self.txt_next_service_mileage.text or None,
            "time_start": (
                self.date_picker_time_start.date.isoformat()
                if self.date_picker_time_start.date else None
            ),
            "time_end": (
                self.date_picker_time_end.date.isoformat()
                if self.date_picker_time_end.date else None
            ),
            "efficiency": (self.txt_efficiency.text or "").strip() or None,
        }

        anvil.server.call(
            'saveConfirmationDetails',
            jobCardID,
            remarks,
            signature,
            createdAt,
            verify_checklist_data
        )
        anvil.server.call_s('updateJobCardStatus', jobCardID, status)
        Notification("Verification saved successfully", style="warning", timeout=3).show()

        # Close Form
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value=True)
        get_open_form().btn_Workflow_click()
