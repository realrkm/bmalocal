from ._anvil_designer import ClientTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import ModGetData
import anvil.js
import re


class Client(ClientTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._prewarmed_edit_client = None
        self._attach_hover_prewarm()

    def _prewarm_edit_modal(self, _evt=None):
        if getattr(self, "_prewarmed_edit_client", None) is not None:
            return
        try:
            from ..EditClient import EditClient
            self._prewarmed_edit_client = EditClient()
        except Exception:
            pass

    def _attach_hover_prewarm(self):
        get_dom = getattr(anvil.js, "get_dom_node", None)
        btn = getattr(self, "btn_EditClient", None)
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
        self.btn_SaveAndNew.enabled = False #Disable button to prevent multiple clicks 
        
        name = self.txt_name.text.strip().upper()
        phone = self.txt_phone.text.strip()
        if self.txt_address.text is not None:
            address = self.txt_address.text.strip()
        else:
            address = self.txt_address.text
        if self.txt_email.text is not None:
            email = self.txt_email.text.strip()
        else:
            email = self.txt_email.text
        narration = self.txt_narration.text
    
        # Validation
        if not name:
            Notification("Please enter client's full name.", style="warning", timeout=3).show()
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
            Notification("Please enter client's phone number.", style="warning", timeout=3).show()
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
        
        # Call server function
        duplicate = anvil.server.call('check_duplicate_contact', "Client", phone)
        if duplicate:
            Notification("Sorry, a client with that phone number has already been added. Please enter another phone number", title="Duplicate Phone Number", style="warning", timeout=3).show()
            self.txt_phone.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled =True
            return

        # Save data     
        anvil.server.call('save_client_data', name, phone, address, email, narration)
        Notification("Client saved successfully.", style="warning", timeout=3).show()
        
        # Clear form
        self.clear_form_fields()                     

    def clear_form_fields(self):
        """Helper function to clear all form fields after saving"""
        self.txt_name.text = ""
        self.txt_phone.text = ""
        self.txt_address.text = ""
        self.txt_email.text = ""
        self.txt_narration.text = ""
    
        # Reset focus to the first field
        self.txt_name.focus()

        # Re-enable Save button in case it was disabled
        self.btn_SaveAndNew.enabled = True
    
    def btn_EditClient_click(self, **event_args):
        """Open pre-warmed EditClient modal in milliseconds."""
        from ..EditClient import EditClient
        modal = self._prewarmed_edit_client or EditClient()
        self._prewarmed_edit_client = None
        alert(content=modal, buttons=[], dismissible=False, large=True)
        try:
            anvil.js.window.setTimeout(self._prewarm_edit_modal, 0)
        except Exception:
            pass

