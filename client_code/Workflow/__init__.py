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
        
        self.permissions = permissions

        # Apply permissions to buttons and load the first available subform
        self.apply_permissions()
        self._rt_token = None
        self._rt_conn_token = None
        self.set_event_handler("hide", self.form_hide)

        # Defer dashboard metrics fetch so the Workflow UI renders instantly
        anvil.js.window.setTimeout(self.load_dashboard_data, 10)
                    
    def apply_permissions(self):
        """Apply only WORKFLOW-related permissions and load the available subforms."""
        workflow_perms = self.permissions.get("WORKFLOW", {"main": False, "subs": {}})
        subs = workflow_perms.get("subs", {})

        statuses = [
            "Checked In",
            "Create Quote",
            "Confirm Quote",
            "In Service",
            "Verify Task",
            "Issue Invoice",
            "Ready for Pickup"
        ]

        allowed_items = [s for s in statuses if subs.get(s)]
        self.cmbStatus.items = allowed_items

    def add_item(self, new_item):
        items = list(self.cmbStatus.items or [])
        items.append(new_item)
        self.cmbStatus.items = items

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def _sync_timer_with_ws(self):
        """Run fallback timer only when WebSocket is disconnected."""
        if not hasattr(self, 'timer_update'):
            return
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            ws_live = bool(rt and rt.isConnected())
        except Exception:
            ws_live = False
        if ws_live:
            self.timer_update.interval = 0
            self.timer_update.enabled = False
        else:
            self.timer_update.interval = 60
            self.timer_update.enabled = True

    def _on_jobcard_event(self, evt=None):
        self.load_dashboard_data()
        if self.cmbStatus.selected_value and self.vehicle_repeater.visible:
            try:
                with anvil.server.no_loading_indicator:
                    self.populateCards(self.cmbStatus.selected_value, self.cmbRegNo.selected_value)
            except Exception as e:
                print(f"Workflow realtime card refresh skipped: {e}")

    def form_show(self, **event_args):
        """Set up WebSocket-driven updates (fallback timer only when WS offline)."""
        self.form_hide()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_token = rt.subscribe("jobcards", self._on_jobcard_event)
                def _on_conn(status):
                    self._sync_timer_with_ws()
                    if status and status.get("reconnected"):
                        self._on_jobcard_event()
                self._rt_conn_token = rt.onConnectionChange(_on_conn)
        except Exception:
            pass
        self._sync_timer_with_ws()

    def form_hide(self, **event_args):
        if hasattr(self, 'timer_update'):
            self.timer_update.interval = 0
            self.timer_update.enabled = False
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                if self._rt_token:
                    rt.unsubscribe(self._rt_token)
                if self._rt_conn_token:
                    rt.offConnectionChange(self._rt_conn_token)
        except Exception:
            pass
        self._rt_token = None
        self._rt_conn_token = None

    def timer_update_tick(self, **event_args):
        """Fallback refresh when WebSocket is offline."""
        self.load_dashboard_data()
        
    def load_dashboard_data(self):
        try:
            with anvil.server.no_loading_indicator:
                all_data = anvil.server.call_s('get_all_jobcards_by_status') or {}
                
                def _get_count(key):
                    val = all_data.get(key, 0)
                    return len(val) if isinstance(val, (list, dict, tuple)) else (val or 0)

                self.label_CheckedIn.text = f"1. Checked In: {_get_count('Checked In')}"
                self.label_CreateQuote.text = f"2. Create Quote: {_get_count('Create Quote')}"
                self.label_ConfirmQuote.text = f"3. Confirm Quote: {_get_count('Confirm Quote')}"
                self.label_InService.text = f"4. In Service: {_get_count('In Service')}"
                self.label_VerifyTask.text = f"5. Verify Task: {_get_count('Verify Task')}"
                self.label_IssueInvoice.text = f"6. Issue Invoice: {_get_count('Issue Invoice')}"
                self.label_ReadyForPickup.text = f"7. Ready for Pickup: {_get_count('Ready for Pickup')}"

                self.refresh()
        except Exception as e:
            print(f"Workflow load_dashboard_data failed: {e}")
        
    def populateCards(self, status, regNo):
        self.vehicle_repeater.items = []
        self.refresh()

        vehicle_data_source = ModGetData.getTechnicianJobCards(status, regNo)
                        
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
        Notification("All 'Ready for Pickup' jobcards have been updated to 'Complete'", title="Success", style="success", timeout=3).show()

    def cmbRegNo_change(self, **event_args):
        """This method is called when an item is selected"""
        self.vehicle_repeater.visible = True
        self.populateCards(self.cmbStatus.selected_value, self.cmbRegNo.selected_value)
        self.refresh()
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        regNo = self.txt_RegNo.text
        if not regNo:
            Notification("Sorry, please enter RegNo to proceed", title="Blank Field Found", style="warning", timeout=3).show()
            self.txt_RegNo.focus()
            return
        self.cmbRegNo.items = anvil.server.call("getRegNoUsingStatus", None, regNo)
        
