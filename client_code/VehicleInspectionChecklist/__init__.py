from ._anvil_designer import VehicleInspectionChecklistTemplate
from anvil import *
import anvil.server
import anvil.users
import datetime
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


_REQUIRED_CHECKBOXES = (
    "chk_safety",
    "chk_jack",
    "chk_chock",
    "chk_ppe",
    "chk_valuables",
    "chk_complain",
    "chk_test_drive",
    "chk_scan",
    "chk_service",
    "chk_oil_level",
    "chk_oil_filter",
    "chk_air_filter",
    "chk_coolant",
    "chk_belt",
    "chk_battery",
    "chk_carriage",
    "chk_front_arms",
    "chk_rear_diff",
    "chk_shocks",
    "chk_exhaust",
    "chk_shaft",
    "chk_oil_leaks",
    "chk_brakes",
    "chk_front_pads",
    "chk_rear_pads",
    "chk_brake_fluid",
    "chk_tyre_pressure",
    "chk_final",
    "chk_torque",
    "chk_road_test",
    "chk_engine_clean",
    "chk_old_parts",
    "chk_invoice_explain",
)

_REQUIRED_TEXTBOXES = (
    "text_box_test_drive",
    "text_box_fault_code",
    "text_box_faults_cleared",
    "text_box_cracks",
    "text_box_voltage",
    "text_box_cca",
    "text_box_any_play",
    "text_box_any_issue",
    "text_box_broken",
    "text_box_rattles",
    "text_box_vibration",
    "text_box_oil_leaks",
    "text_box_front_pad_thickness",
    "text_box_front_disc",
    "text_box_rear_pad_thickness",
    "text_box_17",
    "text_box_18",
    "text_box_22",
    "text_box_tyre_tread",
    "txt_next_service_mileage",
    "txt_efficiency",
)

_REQUIRED_PHOTOS = (
    ("image_1", "Car on jack stands"),
    ("image_2", "Fault or old part"),
    ("image_3", "Dashboard with no warning lights"),
)
_PHOTO_UPLOADS = {
    "image_1": "file_loader_1",
    "image_2": "file_loader_2",
    "image_3": "file_loader_3",
}

_REQUIRED_DATEPICKERS = (
    "date_picker_next_service",
    "date_picker_time_start",
    "date_picker_time_end",
)


class VehicleInspectionChecklist(VehicleInspectionChecklistTemplate):
    def __init__(self, jobcardid, **properties):
        # Set Form properties and Data Bindings.
        super().__init__(**properties)

        # Any code you write here will run before the form opens.
        self.jobcardid = jobcardid
        self._inspection_data_loaded = False
        self._existing_inspection_images = {
            image_name: None for image_name, _ in _REQUIRED_PHOTOS
        }
        self._load_existing_inspection_data()

    @staticmethod
    def _parse_saved_date(value):
        if value is None or value == "":
            return None
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return value
        if not isinstance(value, str):
            raise ValueError("Invalid saved inspection date.")
        if "T" in value:
            return datetime.datetime.fromisoformat(value)
        return datetime.date.fromisoformat(value)

    def _load_existing_inspection_data(self):
        self._inspection_data_loaded = False
        try:
            data = anvil.server.call("get_vehicle_inspection_data", self.jobcardid)
            if not isinstance(data, dict):
                raise ValueError("Invalid saved inspection data.")

            checkboxes = data.get("checkboxes", {})
            textboxes = data.get("textboxes", {})
            dates = data.get("dates", {})
            images = data.get("images", {})
            if not all(
                isinstance(values, dict)
                for values in (checkboxes, textboxes, dates, images)
            ):
                raise ValueError("Invalid saved inspection data.")

            for name in _REQUIRED_CHECKBOXES:
                if name in checkboxes:
                    value = checkboxes[name]
                    if not isinstance(value, bool):
                        raise ValueError("Invalid saved inspection checkbox.")
                    getattr(self, name).checked = value
            for name in _REQUIRED_TEXTBOXES:
                if name in textboxes:
                    value = textboxes[name]
                    getattr(self, name).text = "" if value is None else str(value)
            for name in _REQUIRED_DATEPICKERS:
                if name in dates:
                    getattr(self, name).date = self._parse_saved_date(dates[name])
            for image_name, _ in _REQUIRED_PHOTOS:
                media = images.get(image_name)
                self._existing_inspection_images[image_name] = media
                getattr(self, image_name).source = media

            self._update_hours_worked(notify=False)
            self._inspection_data_loaded = True
        except anvil.server.AppOfflineError:
            Notification(
                "The local server is unreachable. The saved inspection could not be loaded.",
                style="danger",
            ).show()
        except Exception:
            Notification(
                "Unable to load the saved inspection checklist.",
                style="danger",
            ).show()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

    def chk_safety_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_safety.checked:
            self.chk_jack.checked = True
            self.chk_chock.checked = True
            self.chk_ppe.checked = True
            self.chk_valuables.checked = True
        else:
            self.chk_jack.checked = False
            self.chk_chock.checked = False
            self.chk_ppe.checked = False
            self.chk_valuables.checked = False

   
    def chk_complain_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_complain.checked:
            self.chk_test_drive.checked=True
            self.chk_scan.checked=True
            
        else:
            self.chk_test_drive.checked=False
            self.chk_scan.checked=False
           
    def chk_service_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_service.checked:
            self.chk_oil_level.checked=True
            self.chk_oil_filter.checked=True
            self.chk_air_filter.checked=True
            self.chk_coolant.checked=True
            self.chk_belt.checked=True
            self.chk_battery.checked=True
        else:
            self.chk_oil_level.checked=False
            self.chk_oil_filter.checked=False
            self.chk_air_filter.checked=False
            self.chk_coolant.checked=False
            self.chk_belt.checked=False
            self.chk_battery.checked=False

    def chk_carriage_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_carriage.checked:
            self.chk_front_arms.checked=True
            self.chk_rear_diff.checked=True
            self.chk_shocks.checked=True
            self.chk_exhaust.checked=True
            self.chk_shaft.checked=True
            self.chk_oil_leaks.checked=True
        else:
            self.chk_front_arms.checked=False
            self.chk_rear_diff.checked=False
            self.chk_shocks.checked=False
            self.chk_exhaust.checked=False
            self.chk_shaft.checked=False
            self.chk_oil_leaks.checked=False

    def chk_brakes_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_brakes.checked:
            self.chk_front_pads.checked=True
            self.chk_rear_pads.checked=True
            self.chk_brake_fluid.checked=True
            self.chk_tyre_pressure.checked=True
            
        else:
            self.chk_front_pads.checked=False
            self.chk_rear_pads.checked=False
            self.chk_brake_fluid.checked=False
            self.chk_tyre_pressure.checked=False

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

    def file_loader_1_change(self, **event_args):
        self.image_1.source = self.file_loader_1.file

    def file_loader_2_change(self, **event_args):
        self.image_2.source = self.file_loader_2.file

    def file_loader_3_change(self, **event_args):
        self.image_3.source = self.file_loader_3.file

    @staticmethod
    def _component_label(component, name):
        label = getattr(component, "text", "") or getattr(component, "placeholder", "")
        return str(label).strip().rstrip(":") or name.replace("_", " ")

    @staticmethod
    def _format_missing_fields(category, fields):
        shown_fields = fields[:3]
        message = f"{category}: {', '.join(shown_fields)}"
        if len(fields) > len(shown_fields):
            message += f", and {len(fields) - len(shown_fields)} more"
        return message

    def _text_value(self, name):
        value = getattr(self, name).text
        return str(value) if value is not None else ""

    def _collect_checklist_data(self):
        component_names = (
            _REQUIRED_CHECKBOXES
            + _REQUIRED_TEXTBOXES
            + _REQUIRED_DATEPICKERS
        )
        return {
            "checkboxes": {
                name: getattr(self, name).checked for name in _REQUIRED_CHECKBOXES
            },
            "textboxes": {
                name: self._text_value(name) for name in _REQUIRED_TEXTBOXES
            },
            "dates": {
                name: getattr(self, name).date.isoformat()
                for name in _REQUIRED_DATEPICKERS
            },
            "images": {
                image_name: (
                    getattr(self, loader_name).file
                    if getattr(self, loader_name).file not in (None, "")
                    else self._existing_inspection_images.get(image_name)
                )
                for image_name, loader_name in _PHOTO_UPLOADS.items()
            },
            "labels": {
                name: self._component_label(getattr(self, name), name)
                for name in component_names
            },
        }

    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        if not self._inspection_data_loaded:
            Notification(
                "The saved inspection could not be loaded. Close and reopen the checklist before updating.",
                style="danger",
            ).show()
            return

        missing_checkboxes = [
            self._component_label(getattr(self, name), name)
            for name in _REQUIRED_CHECKBOXES
            if not getattr(self, name).checked
        ]
        missing_textboxes = [
            self._component_label(getattr(self, name), name)
            for name in _REQUIRED_TEXTBOXES
            if not self._text_value(name).strip()
        ]
        missing_dates = [
            self._component_label(getattr(self, name), name)
            for name in _REQUIRED_DATEPICKERS
            if getattr(self, name).date is None
        ]
        missing_photos = [
            description
            for name, description in _REQUIRED_PHOTOS
            if (
                getattr(self, _PHOTO_UPLOADS[name]).file in (None, "")
                and self._existing_inspection_images.get(name) is None
            )
        ]

        missing_fields = []
        if missing_checkboxes:
            missing_fields.append(
                self._format_missing_fields("Unchecked checkboxes", missing_checkboxes)
            )
        if missing_textboxes:
            missing_fields.append(
                self._format_missing_fields("Blank text boxes", missing_textboxes)
            )
        if missing_dates:
            missing_fields.append(
                self._format_missing_fields("Blank dates", missing_dates)
            )
        if missing_photos:
            missing_fields.append(
                self._format_missing_fields("Missing photos", missing_photos)
            )

        if missing_fields:
            Notification(
                "Complete the required inspection items before updating:\n"
                + "\n".join(missing_fields),
                title="Incomplete Inspection Checklist",
                style="warning",
            ).show()
            return

        self.btn_Update.enabled = False
        try:
            anvil.server.call(
                "save_update_vehicle_inspection",
                self.jobcardid,
                self._collect_checklist_data(),
            )
        except anvil.server.AppOfflineError:
            Notification(
                "The local server is unreachable. The inspection could not be updated.",
                style="danger",
            ).show()
            return
        except Exception:
            Notification(
                "Unable to update the saved inspection checklist.",
                style="danger",
            ).show()
            return
        finally:
            self.btn_Update.enabled = True

        Notification("Inspection checklist updated.", style="success").show()
        self.btn_Close_click()

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

    def btn_Download_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Download.enabled = False
        media_object = anvil.server.call("downloadInspectionChecklistPdf", self.jobcardid, "InspectionChecklist")
        anvil.media.download(media_object)
        self.deleteFile(self.jobcardid, "InspectionChecklist")
        self.btn_Download.enabled = True

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    