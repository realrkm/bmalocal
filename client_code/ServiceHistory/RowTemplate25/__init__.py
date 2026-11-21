from ._anvil_designer import RowTemplate25Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


def _build_inspection_panel(inspection_data):
    """Build a read-only ColumnPanel displaying saved inspection photos and checklist."""
    panel = ColumnPanel()
    images = inspection_data.get("images", {}) if isinstance(inspection_data, dict) else {}
    checklist = inspection_data.get("checklist", []) if isinstance(inspection_data, dict) else []

    photo_entries = [
        ("Inspection Photo 1", images.get("image_1")),
        ("Inspection Photo 2", images.get("image_2")),
        ("Inspection Photo 3", images.get("image_3")),
    ]
    available_photos = [(label, media) for label, media in photo_entries if media is not None]

    if available_photos:
        panel.add_component(Label(text="Inspection Photos", bold=True, font_size=16))
        for label, media in available_photos:
            panel.add_component(Label(text=label, bold=True))
            panel.add_component(Image(source=media, display_mode="shrink_to_fit", height=220))

    if checklist:
        panel.add_component(Label(text="Inspection Checklist Findings", bold=True, font_size=16))
        grouped = {}
        section_order = []
        for entry in checklist:
            title = entry.get("section_title") or entry.get("section_code") or "Inspection"
            if title not in grouped:
                grouped[title] = []
                section_order.append(title)
            grouped[title].append(entry)

        for section_title in section_order:
            panel.add_component(Label(text=section_title, bold=True, foreground="#0056D6"))
            for item in grouped[section_title]:
                mark = "✓" if item.get("is_checked") else "○"
                desc = item.get("item_description") or item.get("item_code") or ""
                line = f"{mark} {desc}"
                fields = [
                    f
                    for f in (item.get("fields") or [])
                    if isinstance(f, dict) and f.get("value") not in ("", None)
                ]
                if fields:
                    field_bits = []
                    for field in fields:
                        label = field.get("label") or field.get("name") or ""
                        val = field.get("value")
                        val_text = ("Yes" if val else "No") if isinstance(val, bool) else str(val)
                        field_bits.append(f"{label}: {val_text}")
                    line += "\n    " + " | ".join(field_bits)
                panel.add_component(Label(text=line))

    if not available_photos and not checklist:
        panel.add_component(
            Label(text="No saved inspection checklist items or photos were found for this visit.")
        )

    return panel


class RowTemplate25(RowTemplate25Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        super().__init__(**properties)

        # Any code you write here will run before the form opens.
        if isinstance(self.item, dict) and self.item.get("has_inspection"):
            btn = Button(
                text="View Inspection",
                role="primary-color",
                background="#0056D6",
                foreground="white",
                font="Mozilla Headline",
                font_size=14,
            )
            btn.set_event_handler("click", self.btn_view_inspection_click)
            self.add_component(btn, column="KUOHHY")

    def btn_view_inspection_click(self, **event_args):
        """Lazy-load and display inspection checklist findings and photos in a modal."""
        jobcard_id = self.item.get("jobcard_id") if isinstance(self.item, dict) else None
        jobcard_ref = self.item.get("jobcard_ref", "") if isinstance(self.item, dict) else ""
        if not jobcard_id:
            return

        try:
            inspection = anvil.server.call("get_service_history_inspection", int(jobcard_id))
            panel = _build_inspection_panel(inspection)
            alert(
                content=panel,
                title=f"Inspection Details — {jobcard_ref or f'#{jobcard_id}'}",
                large=True,
                buttons=[("Close", True)],
            )
        except Exception as exc:
            Notification(
                str(exc) or "Failed to load inspection details.",
                title="Inspection Error",
                style="danger",
                timeout=4,
            ).show()
