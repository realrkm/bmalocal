from ._anvil_designer import WorkflowTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from datetime import date
from .. import ModGetData

class Workflow(WorkflowTemplate):
    def __init__(self, permissions, **properties):
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors) #Set global server error handler
        self.load_dashboard_data()
        self.total_label.text = "Total Vehicles: 0"
        self.permissions = permissions

        # Apply permissions to buttons and load the first available subform
        self.apply_permissions()
        user = anvil.users.get_user()
        if user['role_id']==1:
            self.btn_TransitionToComplete.visible=True
        else:
            self.btn_TransitionToComplete.visible=False

    def apply_permissions(self):
        """Apply only WORKFLOW-related permissions and load the first available subform."""
        workflow_perms = self.permissions.get("WORKFLOW", {"main": False, "subs": {}})

        first_visible = None  # track which dropdown item to load first

        for subsection, value in workflow_perms["subs"].items():
            if subsection == "Checked In":
                if value and first_visible is None:
                    first_visible = "Checked In"
                    self.add_item(first_visible)
                    first_visible = None #Reset to None to enable addition of other items in the dropdown

            elif subsection == "Create Quote":
                if value and first_visible is None:
                    first_visible = "Create Quote"
                    self.add_item(first_visible)
                    first_visible = None
                    

            elif subsection == "Confirm Quote":
                if value and first_visible is None:
                    first_visible = "Confirm Quote"
                    self.add_item(first_visible)
                    first_visible = None

            elif subsection == "In Service":
                if value and first_visible is None:
                    first_visible = "In Service"
                    self.add_item(first_visible)
                    first_visible = None
                    
            elif subsection == "Verify Task":
                if value and first_visible is None:
                    first_visible = "Verify Task"
                    self.add_item(first_visible)
                    first_visible = None

            elif subsection == "Issue Invoice":
                if value and first_visible is None:
                    first_visible = "Issue Invoice"
                    self.add_item(first_visible)
                    first_visible = None

            elif subsection == "Ready for Pickup":
                if value and first_visible is None:
                    first_visible = "Ready for Pickup"
                    self.add_item(first_visible)
                    first_visible = None


    def add_item(self, new_item):
        items = list(self.cmbStatus.items or [])
        items.append(new_item)
        self.cmbStatus.items = items

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)   
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def form_show(self, **event_args):
        """Set up real-time updates for dashboard forms"""
        if hasattr(self, 'timer_update'):
            self.timer_update.interval = 30  # 30 seconds
            self.timer_update.enabled = True
    
    def timer_update_tick(self, **event_args):
        """Refresh dashboard data"""
        self.load_dashboard_data()
        
    def load_dashboard_data(self):
        all_data = anvil.server.call_s('get_all_jobcards_by_status')
        self.label_CheckedIn.text = f"1. Checked In: {len(all_data.get('Checked In', []))}"
        self.label_CreateQuote.text = f"2. Create Quote: {len(all_data.get('Create Quote', []))}"
        self.label_ConfirmQuote.text = f"3. Confirm Quote: {len(all_data.get('Confirm Quote', []))}"
        self.label_InService.text = f"4. In Service: {len(all_data.get('In Service', []))}"
        self.label_VerifyTask.text = f"5. Verify Task: {len(all_data.get('Verify Task', []))}"
        self.label_IssueInvoice.text = f"6. Issue Invoice: {len(all_data.get('Issue Invoice', []))}"
        self.label_ReadyForPickup.text = f"7. Ready for Pickup: {len(all_data.get('Ready for Pickup', []))}"

        self.refresh()
        
    def populateCards(self, status, regNo):
        self.vehicle_repeater.items = []
        self.refresh()

        vehicle_data_source = ModGetData.getTechnicianJobCards(status, regNo)
                    
        # Set the total
        self.total_label.text = f"Total Vehicles: {len(vehicle_data_source)}"
        self.total_label.visible = True
    
        # Group vehicles into pairs
        group_size = 3 #Since we are displaying 3 items per row
        grouped_vehicles = []
        
        for i in range(0, len(vehicle_data_source), group_size):
            group = vehicle_data_source[i:i+group_size]  # returns up to 3 items
            grouped_dict = {
                "left": group[0] if len(group) > 0 else None,
                "middle": group[1] if len(group) > 1 else None,
                "right": group[2] if len(group) > 2 else None,
                "permissions": self.permissions.get("WORKFLOW", {}).get("subs", {})
            }
            grouped_vehicles.append(grouped_dict)
            
        self.vehicle_repeater.items = grouped_vehicles

    def cmbStatus_change(self, **event_args):
        """This method is called when an item is selected"""
        self.txt_RegNo.text = ""
        self.cmbRegNo.selected_value = None
        self.cmbRegNo.items = anvil.server.call("getRegNoUsingStatus", self.cmbStatus.selected_value,None)
        self.vehicle_repeater.visible = True
        self.populateCards(self.cmbStatus.selected_value, None)
        self.refresh()

    def btn_TransitionToComplete_click(self, **event_args):
        """This method is called when the button is clicked"""
        anvil.server.call("transitionreadyforpickuptocomplete")
        alert("All 'Ready for Pickup' jobcards have been updated to 'Complete'", title="Success")

    def cmbRegNo_change(self, **event_args):
        """This method is called when an item is selected"""
        self.vehicle_repeater.visible = True
        self.populateCards(self.cmbStatus.selected_value, self.cmbRegNo.selected_value)
        self.refresh()
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        regNo = self.txt_RegNo.text
        if not regNo:
            alert("Sorry, please enter RegNo to proceed", title="Blank Field Found")
            self.txt_RegNo.focus()
            return
        self.cmbRegNo.items = anvil.server.call("getRegNoUsingStatus", None, regNo)
        
