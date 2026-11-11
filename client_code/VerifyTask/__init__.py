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
import datetime
from .. import ModGetData

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
        self.chk_road_test.checked = bool(
            data.get("chk_road_test", data.get("chk_test", False))
        )
        self.chk_engine_clean.checked = bool(
            data.get("chk_engine_clean", data.get("chk_clean", False))
        )
        self.chk_old_parts.checked = bool(
            data.get("chk_old_parts", data.get("chk_old", False))
        )
        self.chk_invoice_explain.checked = bool(
            data.get("chk_invoice_explain", data.get("chk_explain", False))
        )
        self.chk_final.checked = bool(
            data.get(
                "chk_final",
                all(
                    checkbox.checked
                    for checkbox in (
                        self.chk_torque,
                        self.chk_road_test,
                        self.chk_engine_clean,
                        self.chk_old_parts,
                        self.chk_invoice_explain,
                    )
                ),
            )
        )

        if data.get("next_service_date"):
            try:
                self.date_picker_next_service.date = datetime.datetime.strptime(
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
                self.date_picker_time_start.date = datetime.datetime.fromisoformat(
                    data["time_start"]
                )
            except ValueError:
                pass

        if data.get("time_end"):
            try:
                self.date_picker_time_end.date = datetime.datetime.fromisoformat(
                    data["time_end"]
                )
            except ValueError:
                pass

        self.txt_efficiency.text = data.get("efficiency") or ""
        self._update_hours_worked(notify=False)

    def _update_hours_worked(self, notify=True):
        start = self.date_picker_time_start.date
        end = self.date_picker_time_end.date
        if start is None or end is None:
            self.lbl_hrs.text = "Total hrs: --"
            return

        if isinstance(start, datetime.date) and not isinstance(start, datetime.datetime):
            start = datetime.datetime.combine(start, datetime.time.min)
        if isinstance(end, datetime.date) and not isinstance(end, datetime.datetime):
            end = datetime.datetime.combine(end, datetime.time.min)

        elapsed_seconds = (end - start).total_seconds()
        if elapsed_seconds < 0:
            self.lbl_hrs.text = "Total hrs: --"
            if notify:
                Notification(
                    "End date and time cannot be earlier than the start date and time.",
                    style="warning",
                ).show()
            return

        elapsed_hours = elapsed_seconds / 3600
        self.lbl_hrs.text = f"Total hrs: {elapsed_hours:.2f}"
               
    def date_picker_time_start_change(self, **event_args):
        self._update_hours_worked()

    def date_picker_time_end_change(self, **event_args):
        self._update_hours_worked()

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
            self.chk_final.checked,
            self.chk_torque.checked,
            self.chk_road_test.checked,
            self.chk_engine_clean.checked,
            self.chk_old_parts.checked,
            self.chk_invoice_explain.checked, 
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
        createdAt = datetime.datetime.now()
        status = self.cmbWorkflow.selected_value

        verify_checklist_data = {
            "chk_final": bool(self.chk_final.checked),
            "chk_torque": bool(self.chk_torque.checked),
            "chk_road_test": bool(self.chk_road_test.checked),
            "chk_engine_clean": bool(self.chk_engine_clean.checked),
            "chk_old_parts": bool(self.chk_old_parts.checked),
            "chk_invoice_explain": bool(self.chk_invoice_explain.checked),
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


    def chk_final_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_final.checked:
            self.chk_torque.checked=True
            self.chk_road_test.checked=True
            self.chk_engine_clean.checked=True
            self.chk_old_parts.checked=True
            self.chk_invoice_explain.checked=True 
        else:
            self.chk_torque.checked=False
            self.chk_road_test.checked=False
            self.chk_engine_clean.checked=False
            self.chk_old_parts.checked=False
            self.chk_invoice_explain.checked=False
