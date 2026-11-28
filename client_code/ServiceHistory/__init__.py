from ._anvil_designer import ServiceHistoryTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


def _format_multiline(text):
    cleaned = str(text or "").strip()
    if not cleaned:
        return "—"
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if len(lines) <= 1:
        return lines[0] if lines else "—"
    return "\n".join(f"• {line}" for line in lines)


def _format_parts(parts):
    if not isinstance(parts, list) or not parts:
        return "—"
    formatted = []
    for part in parts:
        item = str(part.get("item") or "").strip()
        if not item:
            continue
        part_no = str(part.get("part_no") or "").strip()
        qty = str(part.get("quantity") or "").strip()
        entry = f"• {item}"
        if part_no:
            entry += f" [{part_no}]"
        if qty:
            entry += f" × {qty}"
        formatted.append(entry)
    return "\n".join(formatted) if formatted else "—"


def format_service_history_rows(records):
    """Format server service history records to match data_grid_1 column data_keys."""
    rows = []
    for rec in records or []:
        jobcard_ref = str(rec.get("jobcard_ref") or "—")
        status = str(rec.get("status") or "Historical")
        jobcard_status = f"{jobcard_ref}\n({status})"

        mileage_val = rec.get("mileage")
        visit_mileage = (
            f"{mileage_val} km"
            if mileage_val not in ("", None)
            else "—"
        )
        next_val = str(rec.get("next_service_mileage") or "").strip()
        next_mileage = f"Next: {next_val} km" if next_val else "Next: —"

        defects_notes_parts = []
        defects = str(rec.get("defects") or "").strip()
        notes = str(rec.get("notes") or "").strip()
        if defects:
            defects_notes_parts.append(f"Defects:\n{_format_multiline(defects)}")
        if notes:
            defects_notes_parts.append(f"Notes:\n{_format_multiline(notes)}")
        defects_notes = "\n\n".join(defects_notes_parts) if defects_notes_parts else "—"

        has_inspection = bool(rec.get("has_inspection"))

        rows.append({
            "jobcard_id": rec.get("jobcard_id"),
            "jobcard_ref": jobcard_ref,
            "has_inspection": has_inspection,
            "date": str(rec.get("date") or "—"),
            "jobcardstatus": jobcard_status,
            "technician": str(rec.get("technician") or "—"),
            "mileage": f"{visit_mileage}\n{next_mileage}",
            "clientinstructions": _format_multiline(rec.get("client_instruction")),
            "defectsnotes": defects_notes,
            "workdone": _format_multiline(rec.get("work_done")),
            "partsservices": _format_parts(rec.get("parts_and_services")),
            "inspection": "" if has_inspection else "—",
        })
    return rows


class ServiceHistory(ServiceHistoryTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        super().__init__(**properties)

        # Any code you write here will run before the form opens.
        self.repeating_panel_1.items = []
        self.label_3.visible=False
        self.label_4.visible=False
        self._rt_tokens = []
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

    def _unsubscribe_realtime(self):
        try:
            import anvil.js
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                for tok in self._rt_tokens:
                    rt.unsubscribe(tok)
        except Exception:
            pass
        self._rt_tokens = []

    def form_show(self, **event_args):
        self._unsubscribe_realtime()
        try:
            import anvil.js
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_tokens = [
                    rt.subscribe("jobcards", self._on_data_changed),
                    rt.subscribe("payments", self._on_data_changed),
                ]
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._unsubscribe_realtime()

    def _on_data_changed(self, evt=None):
        reg_no = (self.txt_VehicleReg.text or "").strip()
        if not reg_no or not self.repeating_panel_1.items:
            return
        with anvil.server.no_loading_indicator:
            response = anvil.server.call("get_vehicle_service_history", reg_no)
            records = response.get("records", []) if isinstance(response, dict) else []
            if records:
                self.repeating_panel_1.items = format_service_history_rows(records)

    def btn_SearchJobcard_click(self, **event_args):
        """Search exact vehicle registration and populate data_grid_1."""
        reg_no = (self.txt_VehicleReg.text or "").strip()
        if not reg_no:
            self.repeating_panel_1.items = []
            Notification(
                "Please enter an exact vehicle registration number.",
                title="Blank Field",
                style="warning",
                timeout=3,
            ).show()
            return

        self.btn_Search.enabled = False
        try:
            response = anvil.server.call("get_vehicle_service_history", reg_no)
            records = response.get("records", []) if isinstance(response, dict) else []
            display_reg = (
                response.get("reg_no") if isinstance(response, dict) and response.get("reg_no") else reg_no.upper()
            )
            make_model = (
                response.get("make_and_model") if isinstance(response, dict) else ""
            )

            if not records:
                self.repeating_panel_1.items = []
                Notification(
                    f"No service history found for registration {reg_no.upper()}.",
                    title="Not Found",
                    style="warning",
                    timeout=4,
                ).show()
                return

            visit_label = "Visit" if len(records) == 1 else "Visits"
            vehicle_meta = f" ({make_model})" if make_model else ""
            self.label_3.visible=True
            self.label_4.visible=True
            self.label_3.text = f"{vehicle_meta}"
            self.label_4.text = f"{len(records)} {visit_label}"
            self.repeating_panel_1.items = format_service_history_rows(records)
        except Exception as exc:
            self.repeating_panel_1.items = []
            Notification(
                str(exc) or "Failed to load vehicle service history.",
                title="Search Error",
                style="danger",
                timeout=4,
            ).show()
        finally:
            self.btn_Search.enabled = True
