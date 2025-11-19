from ._anvil_designer import ItemTemplate1Template
from anvil import *
import anvil.server
from ...TechnicianDefectsAndRequestedParts import TechnicianDefectsAndRequestedParts
from ...Quote import Quote
from ...ConfirmQuote import ConfirmQuote
from ...InServiceForm import InServiceForm
from ...VerifyTask import VerifyTask
from ...Invoice import Invoice

class ItemTemplate1(ItemTemplate1Template):

    STATUS_TO_BUTTON = {
        "Checked In": "TECHNICIAN REVIEW",
        "Create Quote": "CREATE QUOTE",
        "Confirm Quote": "CONFIRM QUOTE",
        "In Service": "IN SERVICE",
        "Verify Task": "VERIFY TASK",
        "Issue Invoice": "ISSUE INVOICE"
    }

    def __init__(self, **properties):
        self.init_components(**properties)

        self.permissions = self.item.get("permissions", {})

        # Build 3 cards using one shared function
        self._build_card(self.item.get("left"), self.left_card_panel, 
                         self.button_details, prefix="")
        self._build_card(self.item.get("middle"), self.middle_card_panel, 
                         self.button_details_1, prefix="_1")
        self._build_card(self.item.get("right"), self.right_card_panel, 
                         self.button_details_2, prefix="_2")


    # ------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------
    def has_permission(self, status):
        """Return True if this user has permission for this status."""
        return self.permissions.get(status, False)

    def _build_card(self, data, panel, button, prefix=""):
        """Generic builder for left/middle/right cards."""
        if not data:
            panel.visible = False
            return

        # Fill labels dynamically using prefix
        getattr(self, f"id{prefix}").text = str(data["id"])
        getattr(self, f"label_make{prefix}").text = f"Make: {data['make']}"
        getattr(self, f"label_owner{prefix}").text = f"Job Card Ref: {data['jobcardref']}"
        getattr(self, f"label_plate{prefix}").text = f"Plate: {data['plate']}"
        getattr(self, f"label_chassis{prefix}").text = f"Chassis: {data['chassis']}"
        getattr(self, f"label_instruction{prefix}").text = f"Instruction: {data['instruction']}"
        getattr(self, f"label_date{prefix}").text = f"Due Date: {data['date'].strftime('%b %d, %Y')}"

        getattr(self, f"label_status{prefix}").text = data["status"]
        getattr(self, f"label_technician{prefix}").text = data["technician"]

        # Color coding (unified)
        getattr(self, f"label_status{prefix}").foreground = "#6AA84F"
        getattr(self, f"label_technician{prefix}").foreground = "#6AA84F"

        # Setup button based on permissions
        status = data["status"]

        if status in self.STATUS_TO_BUTTON and self.has_permission(status):
            button.text = self.STATUS_TO_BUTTON[status]
            button.visible = True
        else:
            button.visible = False


    # ------------------------------------------------------------
    # BUTTON CLICK HANDLERS (LEFT / MIDDLE / RIGHT)
    # ------------------------------------------------------------
    def _handle_button_click(self, btn, record_id, action_text):
        btn.enabled = False
        get_open_form().btn_Workflow_click()

        forms = {
            "TECHNICIAN REVIEW": TechnicianDefectsAndRequestedParts,
            "CREATE QUOTE":     Quote,
            "CONFIRM QUOTE":    ConfirmQuote,
            "IN SERVICE":       InServiceForm,
            "VERIFY TASK":      VerifyTask,
            "ISSUE INVOICE":    Invoice
        }

        form_class = forms.get(action_text)
        if form_class:
            alert(content=form_class(record_id), buttons=[], dismissible=False, large=True)


    # ---- LEFT ----
    def button_details_click(self, **event_args):
        self._handle_button_click(
            self.button_details,
            self.id.text,
            self.button_details.text
        )


    # ---- MIDDLE ----
    def button_details_1_click(self, **event_args):
        self._handle_button_click(
            self.button_details_1,
            self.id_1.text,
            self.button_details_1.text
        )


    # ---- RIGHT ----
    def button_details_2_click(self, **event_args):
        self._handle_button_click(
            self.button_details_2,
            self.id_2.text,
            self.button_details_2.text
        )
