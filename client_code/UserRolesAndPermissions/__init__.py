from ._anvil_designer import UserRolesAndPermissionsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..Roles import Roles
from ..ViewRoles import ViewRoles
import anvil.js

class UserRolesAndPermissions(UserRolesAndPermissionsTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()

        self.drop_down_selectrole.items = anvil.server.call("getRoles")

        # Set checkbox tags
        self.chk_contact.tag = "CONTACT"
        self.chk_clients.tag = "Clients"
        self.chk_technicians.tag = "Technicians"
        self.chk_staffs.tag = "Staff"
        self.chk_jobcard.tag = "JOB CARD"
        self.chk_workflow.tag = "WORKFLOW"
        self.chk_checkedin.tag = "Checked In"
        self.chk_createquote.tag = "Create Quote"
        self.chk_confirmquote.tag = "Confirm Quote"
        self.chk_inservice.tag = "In Service"
        self.chk_verifytask.tag = "Verify Task"
        self.chk_issueinvoice.tag = "Issue Invoice"
        self.chk_readyforpickup.tag = "Ready for Pickup"
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
        self.chk_stocktaking.tag="Stock Taking"
        self.chk_report.tag = "REPORTS"
        self.chk_clientreport.tag = "Client Report"
        self.chk_cardetailsreport.tag = "Car Details Report"
        self.chk_techniciansreport.tag = "Technicians Report"
        self.chk_staffreports.tag = "Staffs Report"
        self.chk_inventoryreport.tag = "Inventory Report"
        self.chk_quoteinvoicereport.tag = "Quote And Invoice Report"
        self.chk_paymentreport.tag = "Payment Report"
        self.chk_MonthlySchedule.tag = "Monthly Schedule"
        self.chk_partshub.tag = "PARTS HUB"
        self.chk_partscatalog.tag = "Parts Catalog"
        self.chk_ordertracking.tag = "Order Tracking"
        self.chk_settings.tag = "SETTINGS"
        self.chk_useraccounts.tag = "User Accounts"
        self.chk_roleasandpermissions.tag = "Roles And Permissions"
        self.chk_reset.tag = "RESET"

        # Define sections with their subsections
        self.sections = {
            "CONTACT": [self.chk_clients, self.chk_technicians, self.chk_staffs],
            "JOB CARD": [],
            "WORKFLOW": [
                self.chk_checkedin, self.chk_createquote, self.chk_confirmquote,
                self.chk_inservice, self.chk_verifytask, self.chk_issueinvoice, self.chk_readyforpickup
            ],
            "TRACKER": [],
            "REVISION": [
                self.chk_interimquote, self.chk_amendedinvoice,
                self.chk_repairpriorities, self.chk_brandcomparison
            ],
            "PAYMENT": [],
            "INVENTORY": [self.chk_addnewparts, self.chk_addmorestock, self.chk_stocktaking],
            "REPORTS": [
                self.chk_clientreport, self.chk_cardetailsreport, self.chk_techniciansreport,
                self.chk_staffreports, self.chk_inventoryreport, self.chk_quoteinvoicereport, 
                self.chk_paymentreport, self.chk_MonthlySchedule
            ],
            "PARTS HUB": [self.chk_partscatalog, self.chk_ordertracking],
            "SETTINGS": [self.chk_useraccounts, self.chk_roleasandpermissions],
            "RESET": [],
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
            "PARTS HUB": self.chk_partshub,
            "SETTINGS": self.chk_settings,
            "RESET": self.chk_reset,
        }

        # Attach handlers only for main checkboxes
        for section, main_chk in self.main_checkboxes.items():
            main_chk.set_event_handler("change", self.main_checkbox_changed)

    # --- Main Checkbox Logic (controls subs) ---
    def main_checkbox_changed(self, **event_args):
        checkbox = event_args['sender']
        section = self.get_section_from_checkbox(checkbox)
        subs = self.sections.get(section, [])
        for sub in subs:
            sub.checked = checkbox.checked

    # --- Helpers ---
    def get_section_from_checkbox(self, checkbox):
        for section, chk in self.main_checkboxes.items():
            if chk == checkbox:
                return section
        return None

    def btn_AddRole_click(self, **event_args):
        alert(content=Roles(), buttons=[], dismissible=False, large=True)
        #Update dropdown component
        self.drop_down_selectrole.items = anvil.server.call_s("getRoles")

    def btn_UpdateRoleAndPermissions_click(self, **event_args):
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
        alert("Permissions saved successfully", title="Success")

        # Reload Form
        self.reset_form()

    def btn_ViewRoles_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=ViewRoles(), buttons=[], dismissible=False, large=True)

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def reset_form(self):
        """Called when resetting the form"""
        # Reload dropdown
        self.drop_down_selectrole.items = anvil.server.call("getRoles")
        self.drop_down_selectrole.selected_value = None

        # Clear all main + sub checkboxes
        for chk in self.main_checkboxes.values():
            chk.checked = False
        for subs in self.sections.values():
            for chk in subs:
                chk.checked = False

        self.refresh()

    

    
