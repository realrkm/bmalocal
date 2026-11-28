from ._anvil_designer import TehniciansTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData
import re


class Tehnicians(TehniciansTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._prewarmed_edit_tech = None
        self._prewarmed_toolkits = None

        cached = getattr(ModGetData, "peekToolkitsCached", lambda: None)()
        if cached is not None:
            self.dropdown_toolkits.items = [(r["ToolkitName"], r) for r in cached]
        else:
            anvil.js.window.setTimeout(self.refresh_toolkits, 0)

        self._attach_hover_prewarm()

    def refresh_toolkits(self, force_refresh=False):
        if hasattr(ModGetData, "getToolkitsCached"):
            toolkits = ModGetData.getToolkitsCached(force_refresh=force_refresh) or []
        else:
            with anvil.server.no_loading_indicator:
                toolkits = anvil.server.call('get_toolkits', None) or []
        self.dropdown_toolkits.items = [(r["ToolkitName"], r) for r in toolkits]

    def _prewarm_edit_tech(self, _evt=None):
        if getattr(self, "_prewarmed_edit_tech", None) is not None:
            return
        try:
            from ..EditTechnician import EditTechnician
            self._prewarmed_edit_tech = EditTechnician()
        except Exception:
            pass

    def _prewarm_toolkits(self, _evt=None):
        if getattr(self, "_prewarmed_toolkits", None) is not None:
            return
        try:
            from ..Toolkits import Toolkits
            self._prewarmed_toolkits = Toolkits()
        except Exception:
            pass

    def _attach_hover_prewarm(self):
        get_dom = getattr(anvil.js, "get_dom_node", None)
        if not callable(get_dom):
            return
        for attr, handler in (
            ("btn_EditTechnician", self._prewarm_edit_tech),
            ("btn_Toolkit", self._prewarm_toolkits),
        ):
            btn = getattr(self, attr, None)
            if btn is None:
                continue
            try:
                dom_node = get_dom(btn)
                dom_node.addEventListener("pointerenter", handler, {"passive": True})
                dom_node.addEventListener("mousedown", handler, {"passive": True})
                dom_node.addEventListener("touchstart", handler, {"passive": True})
            except Exception:
                pass

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_SaveAndNew.enabled = False #Disable button to prevent multiple clicks
    
        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()
        if self.dropdown_toolkits.selected_value is None:
            toolkit = None
        else:
            toolkit = self.dropdown_toolkits.selected_value["ID"]
        
        # Validation
        if not name:
            Notification("Please enter technician's full name.", style="warning", timeout=3).show()
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return
        elif any(char.isdigit() for char in name):
            Notification("Full name should not contain any numbers.", style="warning", timeout=3).show()
            self.txt_name.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return
        elif not phone:
            Notification("Please enter technician's phone number.", style="warning", timeout=3).show()
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled =True
            return
            """
        elif not re.match(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$', phone):
            Notification("Please enter a valid phone number", timeout=3).show()
            self.txt_phone.text = ""
            self.txt_phone.focus()
            self.btn_SaveAndNew.enabled =True
            return
            """
        elif not toolkit:
            Notification("Please select assigned toolkit.", style="warning", timeout=3).show()
            self.dropdown_toolkits.focus()
            self.btn_SaveAndNew.enabled =True
            return


        # Call server function
        duplicate = anvil.server.call('check_duplicate_contact', "Technician", phone)
        if duplicate:
            Notification("Sorry, a technician with that phone number has already been added. Please enter another phone number.", title="Duplicate Phone Number", style="warning", timeout=3).show()
            self.txt_phone.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return

        # Save data
        anvil.server.call('save_technician_data', name, phone, toolkit)
        Notification("Technician saved successfully.", style="warning", timeout=3).show()

        # Clear form
        self.clear_form_fields()

    def clear_form_fields(self):
        """Helper function to clear all form fields after saving without extra server calls."""
        self.txt_name.text = ""
        self.txt_phone.text = ""
        self.dropdown_toolkits.selected_value = None
        self.txt_name.focus()
        self.btn_SaveAndNew.enabled = True

    def btn_EditTechnician_click(self, **event_args):
        """Open pre-warmed EditTechnician modal in milliseconds."""
        from ..EditTechnician import EditTechnician
        modal = self._prewarmed_edit_tech or EditTechnician()
        self._prewarmed_edit_tech = None
        alert(content=modal, buttons=[], dismissible=False, large=True)
        try:
            anvil.js.window.setTimeout(self._prewarm_edit_tech, 0)
        except Exception:
            pass

    def btn_Toolkit_click(self, **event_args):
        """Open pre-warmed Toolkits modal in milliseconds and refresh dropdown if toolkits changed."""
        from ..Toolkits import Toolkits
        modal = self._prewarmed_toolkits or Toolkits()
        self._prewarmed_toolkits = None
        res = alert(content=modal, buttons=[], dismissible=False, large=True)
        if res == "updated":
            self._prewarmed_edit_tech = None
            self.refresh_toolkits(force_refresh=True)
        try:
            anvil.js.window.setTimeout(self._prewarm_toolkits, 0)
        except Exception:
            pass
