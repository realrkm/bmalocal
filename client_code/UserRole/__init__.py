from ._anvil_designer import UserRoleTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class UserRole(UserRoleTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        self.sections = {
            "CONTACT": [self.chk_clients, self.chk_technicians, self.chk_staffs],
            "JOB CARD": [],
            "WORKFLOW": [self.chk_checkedin, self.chk_wf_technicians, self.chk_wf_staffs],
            "TRACKER": [],
            "REVISION": [self.chk_rev_clients, self.chk_rev_technicians, self.chk_rev_staffs],
            "PAYMENT": [],
            "INVENTORY": [self.chk_add_parts, self.chk_add_stocks],
            "REPORTS": [
                self.chk_r_clients, self.chk_r_cardetails, self.chk_r_technicians,
                self.chk_r_staffs, self.chk_r_inventory, self.chk_r_quote, self.chk_r_payment
            ],
        }

        # Map main checkboxes
        self.main_checkboxes = {
            "CONTACT": self.chk_contact,
            "JOB CARD": self.chk_jobcard,
            "WORKFLOW": self.chk_workflow,
            "TRACKER": self.chk_tracker,
            "REVISION": self.chk_revision,
            "PAYMENT": self.chk_payment,
            "INVENTORY": self.chk_inventory,
            "REPORTS": self.chk_reports,
        }
    
        # Attach handlers
        for section, main_chk in self.main_checkboxes.items():
            main_chk.set_event_handler("change", self.main_checkbox_changed)
    
        for section, subs in self.sections.items():
            for sub_chk in subs:
                sub_chk.set_event_handler("change", self.sub_checkbox_changed)
    
    # --- Main Checkbox Logic ---
    def main_checkbox_changed(self, checkbox, **event_args):
        section = self.get_section_from_checkbox(checkbox)
        subs = self.sections.get(section, [])
        for sub in subs:
            sub.checked = checkbox.checked
    
    # --- Sub Checkbox Logic ---
    def sub_checkbox_changed(self, checkbox, **event_args):
        section = self.get_section_from_sub(checkbox)
        main_chk = self.main_checkboxes[section]
        subs = self.sections[section]
    
        if all(sub.checked for sub in subs):
            main_chk.checked = True
        else:
            main_chk.checked = False
    
    # --- Helpers ---
    def get_section_from_checkbox(self, checkbox):
        for section, chk in self.main_checkboxes.items():
            if chk == checkbox:
                return section
        return None
    
    def get_section_from_sub(self, checkbox):
        for section, subs in self.sections.items():
            if checkbox in subs:
                return section
        return None
