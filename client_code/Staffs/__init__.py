from ._anvil_designer import StaffsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
import re


class Staffs(StaffsTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._prewarmed_edit_staff = None
        self._attach_hover_prewarm()

    def _prewarm_edit_modal(self, _evt=None):
        if getattr(self, "_prewarmed_edit_staff", None) is not None:
            return
        try:
            from ..EditStaff import EditStaff
            self._prewarmed_edit_staff = EditStaff()
        except Exception:
            pass

    def _attach_hover_prewarm(self):
        get_dom = getattr(anvil.js, "get_dom_node", None)
        btn = getattr(self, "btn_EditStaff", None)
        if not callable(get_dom) or btn is None:
            return
        try:
            dom_node = get_dom(btn)
            dom_node.addEventListener("pointerenter", self._prewarm_edit_modal, {"passive": True})
            dom_node.addEventListener("mousedown", self._prewarm_edit_modal, {"passive": True})
            dom_node.addEventListener("touchstart", self._prewarm_edit_modal, {"passive": True})
        except Exception:
            pass

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_SaveAndNew.enabled = False  # Disable button to prevent multiple clicks

        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()
       
        # Validation
        if not name:
            Notification("Please enter technician's full name.", style="warning", timeout=3).show()
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return
        elif any(char.isdigit() for char in name):
            Notification("Full name should not contain any numbers.", style="warning", timeout=3).show()
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return
        elif not phone:
            Notification("Please enter technician's phone number.", style="warning", timeout=3).show()
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled = True
            return
            """
        elif not re.match(
            r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$", phone
        ):
            Notification("Please enter a valid phone number", timeout=3).show()
            self.txt_phone.text = ""
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled = True
            return
            """
            
        # Call server function
        duplicate = anvil.server.call("check_duplicate_contact", "Staff", phone)
        if duplicate:
            alert(
                "Sorry, a staff with that phone number has already been added. Please enter another phone number.",
                title="Duplicate Phone Number",
                large=False,
            )
            self.txt_phone.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return

        # Save data
        anvil.server.call("save_staff_data", name, phone)
        Notification("Staff saved successfully.", style="warning", timeout=3).show()

        # Clear form
        self.clear_form_fields()

    def clear_form_fields(self):
        """Helper function to clear all form fields after saving"""
        self.txt_name.text = ""
        self.txt_phone.text = ""
        
        # Reset focus to the first field
        self.txt_name.focus()

        # Re-enable Save button
        self.btn_SaveAndNew.enabled = True

    def btn_EditStaff_click(self, **event_args):
        """Open pre-warmed EditStaff modal in milliseconds."""
        from ..EditStaff import EditStaff
        modal = self._prewarmed_edit_staff or EditStaff()
        self._prewarmed_edit_staff = None
        alert(content=modal, buttons=[], dismissible=False, large=True)
        try:
            anvil.js.window.setTimeout(self._prewarm_edit_modal, 0)
        except Exception:
            pass
