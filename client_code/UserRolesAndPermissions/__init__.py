from ._anvil_designer import UserRolesAndPermissionsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..Roles import Roles


class UserRolesAndPermissions(UserRolesAndPermissionsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        self.drop_down_selectrole.items = anvil.server.call("getRoles")
        #Set checkbox tags
        self.chk_contact.tag = "CONTACT"
        self.chk_clients.tag = "Clients"
        self.chk_technicians.tag = "Technicians"
        self.chk_staffs.tag = "Staffs"
        self.chk_jobcard.tag = "JOB CARDS"
        self.chk_workflow.tag = "WORKFLOW"
        self.chk_checkedin.tag = "Checked In"
        self.chk_createquote.tag = "Create Quote"
        self.chk_confirmquote.tag = "Confirm Quote"
        self.chk_inservice.tag = "In Service"
        self.chk_verifytask.tag = "Verify Task"
        self.chk_issueinvoice.tag = "Issue Invoice"
        self.chk_readyforpickup.tag = "Ready For Pickup"
        self.chk_tracker.tag = "TRACKER"
        self.chk_revision.tag = "REVISION"
        self.chk_interimquote.tag = "Interim Quote"
        self.chk_amendedinvoice.tag = "Amended Invoice"
        self.chk_repairpriorities.tag = "Repair Priorities"
        self.chk_brandcomparison.tag = "Brand Comparison"
        self.chk_payment.tag = "PAYMENT"
        self.chk_inventory.tag ="INVENTORY"
        self.chk_addnewparts.tag = "Add New Parts"
        self.chk_addmorestock.tag = "Add More Stock"
        self.chk_report.tag = "REPORTS"
        self.chk_clientreport.tag = "Client Report"
        self.chk_cardetailsreport.tag = "Car Details Report"
        self.chk_techniciansreport.tag = "Technicians Report"
        self.chk_staffreports.tag = "Staffs Report"
        self.chk_inventoryreport.tag = "Inventory Report"
        self.chk_quoteinvoicereport.tag = "Quote And Invoice Report"
        self.chk_paymentreport.tag = "Payment Report"

        
        # Define sections with their subsections
        self.sections = {
            "CONTACT": [self.chk_clients, self.chk_technicians, self.chk_staffs],
            "JOB CARD": [],
            "WORKFLOW": [self.chk_checkedin, self.chk_createquote, self.chk_confirmquote, self.chk_inservice, self.chk_verifytask, self.chk_issueinvoice, self.chk_readyforpickup],
            "TRACKER": [],
            "REVISION": [self.chk_interimquote, self.chk_amendedinvoice, self.chk_repairpriorities, self.chk_brandcomparison],
            "PAYMENT": [],
            "INVENTORY": [self.chk_addnewparts, self.chk_addmorestock],
            "REPORTS": [
                self.chk_clientreport, self.chk_cardetailsreport, self.chk_techniciansreport,
                self.chk_staffreports, self.chk_inventoryreport, self.chk_quoteinvoicereport, self.chk_paymentreport
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
            "REPORTS": self.chk_report,
        }
    
        # Attach handlers
        for section, main_chk in self.main_checkboxes.items():
            main_chk.set_event_handler("change", self.main_checkbox_changed)
    
        for section, subs in self.sections.items():
            for sub_chk in subs:
                sub_chk.set_event_handler("change", self.sub_checkbox_changed)
    
    # --- Main Checkbox Logic ---
    def main_checkbox_changed(self, **event_args):
        checkbox = event_args['sender']
        section = self.get_section_from_checkbox(checkbox)
        subs = self.sections.get(section, [])
        for sub in subs:
            sub.checked = checkbox.checked
    
    # --- Sub Checkbox Logic ---
    def sub_checkbox_changed(self, **event_args):
        checkbox = event_args['sender']
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

    def btn_AddRole_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=Roles(), buttons=[],dismissible=False, large=True)

    def btn_Save_click(self, **event_args):
        """This method is called when the button is clicked"""
        role_id = self.drop_down_selectrole.selected_value
        
        if not role_id:
            alert("Please select a role before saving permissions.", 
                title="Missing Role", large=False)
            return
    
        selected_permissions = {}
    
        # Collect checked states
        for section, main_chk in self.main_checkboxes.items():
            subs = self.sections.get(section, [])
            selected_permissions[section] = {
                "main": main_chk.checked,
                "subs": {sub.tag: sub.checked for sub in subs}
            }
    
        # ✅ Check if at least one permission is selected
        any_selected = any(
            section_data["main"] or any(section_data["subs"].values())
            for section_data in selected_permissions.values()
        )
    
        if not any_selected:
            alert("Please select at least one permission before saving.",
                title="No Permissions Selected", large=False)
            return
    
        # Send to server
        anvil.server.call("save_user_permissions", role_id, selected_permissions)
        alert(selected_permissions)
        alert("Permissions saved successfully!", title="Success")
        #Reload Form
        get_open_form().btn_Settings_click("ROLES AND PERMISSIONS")

