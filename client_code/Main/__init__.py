from ._anvil_designer import MainTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import ModNavigation
from .. import ModGetData
import anvil.js
from anvil.js.window import navigator, setTimeout
from ..FAQ import FAQ
from ..Alerts import Alerts
from ..IncompleteDefectsInfo import IncompleteDefectsInfo
from ..ViewTechnicianPortalDetails import ViewTechnicianPortalDetails
from ..ViewPricingAlertDetails import ViewPricingAlertDetails
import json
import time

class Main(MainTemplate):

    def __init__(self, **properties):
        self.init_components(**properties)
        anvil.js.call('replaceBanner')

        while anvil.users.get_user() is None:
            anvil.users.login_with_form()

        user = anvil.users.get_user()
        if user:
            self.permissions = anvil.server.call("get_user_permissions", user["role_id"])
            self.apply_permissions()

            if user['role_id'] == 1:
                self.refresh()
            else:
                self.notification_label.visible = False
                self.btn_alerts.visible = False
                self.btn_IncompleteDefectsInfo.visible = False

            user_agent = navigator.userAgent
            anvil.server.call_s('get_stats', user_agent)

            ModNavigation.home_form = self
            self.error_label.visible = False

            set_default_error_handling(
                lambda exc: ModGetData.handle_server_errors(exc, self.error_label)
            )


        # ── Walkie-Talkie State ──────────────────────────────
        self._state = "idle"  # idle | listening | thinking | speaking
        self._pending_text = None

        self.live_popup.visible = False
        self.fab_btn.tooltip = "Click to talk"
        self.fab_btn.enabled = True

        # JS callback bridge
        anvil.js.window["live_assistant_event"] = self._on_assistant_event

    # ─────────────────────────────────────────────
    # FAB CLICK: Toggle listening
    # ─────────────────────────────────────────────

    def fab_btn_click(self, **event_args):
        if self._state == "idle":
            self._start_listening()
        elif self._state == "listening":
            self._stop_listening()  # User manually ended utterance
        # Ignore clicks during thinking/speaking (or add cancel logic if desired)

    # ─────────────────────────────────────────────
    # Listening Controls
    # ─────────────────────────────────────────────

    def _start_listening(self):
        self._state = "listening"
        self._open_popup()
        self.lbl_status.text = "🎤 Listening..."
        self.lbl_transcript.text = "Speak now..."
        self.fab_btn.tooltip = "Click to stop & send"
        self.fab_btn.icon = "fa:stop"
        self.fab_btn.enabled = True

        # Start mic via JS
        started = anvil.js.call_js("window.BMALiveControl.startListening")
        if not started:
            self._on_error("Microphone access denied or not supported")

    def _stop_listening(self):
        if self._state != "listening":
            return
        stopped = anvil.js.call_js("window.BMALiveControl.stopListening")
        if stopped:
            self.lbl_status.text = "⏳ Processing..."
            # Don't change state yet – wait for "final" event from JS

    # ─────────────────────────────────────────────
    # JS Event Handler (unified)
    # ─────────────────────────────────────────────

    def _on_assistant_event(self, event_name, data_json):
        data = json.loads(data_json or "{}")

        if event_name == "interim":
            # Show live transcription while listening
            if self._state == "listening":
                self.lbl_transcript.text = f"You: {data.get('text','')}"

        elif event_name == "final":
            # User finished speaking → send to server
            if self._state == "listening":
                user_text = data.get("text", "").strip()
                if user_text:
                    self._state = "thinking"
                    self.lbl_status.text = "🤔 Thinking..."
                    self.fab_btn.enabled = False  # Prevent interruption
                    self._query_gemma(user_text)
                else:
                    self._return_to_idle()

        elif event_name == "speech_complete":
            # Assistant finished speaking → return to idle
            if self._state == "speaking":
                self._return_to_idle()

        elif event_name == "barge_in":
            # User interrupted assistant
            if self._state in ["thinking", "speaking"]:
                anvil.js.call_js("window.BMALiveControl.cancelSpeech")
                self._return_to_idle()
                self.lbl_status.text = "🎤 Interrupted"

        elif event_name == "status":
            self.lbl_status.text = data.get("text", self.lbl_status.text)

        elif event_name == "error":
            self._on_error(data.get("message", "Unknown error"))

    # ─────────────────────────────────────────────
    # Server Query (blocking, but with timeout)
    # ─────────────────────────────────────────────

    def timer_1_tick(self, **event_args):
        """Poll background task for completion"""
        if not hasattr(self, 'current_task') or not self.current_task:
            return
    
        try:
            # Check if task finished
            if self.current_task.is_complete():
                self.timer_1.enabled = False  # Stop polling
    
                result = self.current_task.get_result()  # Get final response
                if result and result.strip():
                    self._state = "speaking"
                    self.lbl_transcript.text = f"Gemma: {result}"
                    self.lbl_status.text = "🔊 Speaking..."
                    # Speak full response once
                    anvil.js.call_js("window.bmaSpeakFull", result)
                else:
                    self.lbl_transcript.text = "Gemma: (no response)"
                    self._return_to_idle()
                return
    
            # Check for errors during execution
            state = self.current_task.get_state()
            status = state.get('status', '')
    
            if status.startswith('error:'):
                self.timer_1.enabled = False
                self._on_error(status.replace('error: ', ''))
                return
    
            # Optional: Show progress while thinking
            if status == 'thinking':
                dots = "." * ((int(time.time()) % 4))  # Animate: . .. ...
                self.lbl_status.text = f"🤔 Thinking{dots}"
    
        except Exception as e:
            self.timer_1.enabled = False
            self._on_error(f"Task error: {e}")
    
    def _query_gemma(self, user_text):
        try:
            self._state = "thinking"
            self.lbl_status.text = "🤔 Thinking..."
            self.fab_btn.enabled = False  # Prevent interruption during processing
    
            # Launch background task (returns immediately, even on free plan)
            self.current_task = anvil.server.call("ask_gemma_sync", user_text)
    
            # Start polling timer
            self.timer_1.interval = 0.5  # Poll every 500ms
            self.timer_1.enabled = True
    
        except Exception as e:
            self._on_error(f"Failed to start: {e}")
            self._return_to_idle()
        

    def _return_to_idle(self):
        self._state = "idle"
        self.lbl_status.text = "⚪ Ready"
        self.fab_btn.tooltip = "Click to talk"
        self.fab_btn.icon = "fa:microphone"
        self.fab_btn.enabled = True
        # Keep popup open for context, or close if preferred:
        # self._close_popup()

    def _on_error(self, message):
        self._state = "idle"
        self.lbl_status.text = f"❌ {message}"
        self.fab_btn.enabled = True
        self.fab_btn.icon = "fa:microphone"
        print(f"[Assistant Error] {message}")

    # ─────────────────────────────────────────────
    # Popup UI helpers
    # ─────────────────────────────────────────────

    def _open_popup(self):
        self.live_popup.visible = True
        self._popup_open = True

    def btn_close_popup_click(self, **event_args):
        # Cancel any active session when closing popup
        if self._state == "listening":
            anvil.js.call_js("window.BMALiveControl.stopListening")
        elif self._state == "speaking":
            anvil.js.call_js("window.BMALiveControl.cancelSpeech")
        self._return_to_idle()
        self._close_popup()

    def _close_popup(self):
        self.live_popup.visible = False
        self._popup_open = False
            
            
    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def apply_permissions(self):
        """Apply user permissions to the sidebar only"""
        section_map = {
            "CONTACT": self.btn_Contact,
            "JOB CARD": self.btn_JobCard,
            "WORKFLOW": self.btn_Workflow,
            "TRACKER": self.btn_Tracker,
            "REVISION": self.btn_Revision,
            "PAYMENT": self.btn_Payment,
            "INVENTORY": self.btn_Inventory,
            "REPORTS": self.btn_Report,
            "PARTS HUB": self.btn_PartsHub,
            "SETTINGS": self.btn_Settings,
            "RESET": self.btn_ResetPassword,
        }
    
        for section, button in section_map.items():
            section_perms = self.permissions.get(section, {})
            # Hide main button if no access at all
            if not (section_perms.get("main") or any(section_perms.get("subs", {}).values())):
                button.visible = False
                button.enabled = False
            else:
                button.visible = True
                button.enabled = True
                
    def highlight_active_button(self, selected_text):
        # Loop through all buttons in the panel
        for comp in self.column_panel_navigation.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"  # Highlighted black
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"  # Normal blue
                    comp.foreground = "white"
                    
    def load_component(self, cmpt):
        self.column_panel_content.clear()
        self.column_panel_content.add_component(cmpt)
        # Now refresh the page
        self.refresh_data_bindings()
        
    def btn_Contact_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("CONTACT")
        ModNavigation.go_Contact(self.permissions)
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal')
    

    def btn_JobCard_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("JOB CARD")
        ModNavigation.go_JobCard()
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 
        
    def btn_Workflow_click(self, **event_args):
        self.highlight_active_button("WORKFLOW")
        """This method is called when the button is clicked"""
        ModNavigation.go_Workflow(self.permissions)
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 


    def btn_Tracker_click(self, **event_args):
        self.highlight_active_button("TRACKER")
        """This method is called when the button is clicked"""
        ModNavigation.go_Tracker()
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 
        
    def btn_Revision_click(self, **event_args):
        self.highlight_active_button("REVISION")
        ModNavigation.go_Revision(self.permissions)
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 

    def btn_Payment_click(self, **event_args):
        self.highlight_active_button("PAYMENT")
        ModNavigation.go_Payment()
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 
        
    def btn_Inventory_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("INVENTORY")
        ModNavigation.go_Inventory(self.permissions)
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 
        
    def btn_Report_click(self, **event_args):
        self.highlight_active_button("REPORTS")
        ModNavigation.go_Report(self.permissions)
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 

    def btn_PartsHub_click(self, **event_args):
        self.highlight_active_button("PARTS HUB")
        ModNavigation.go_PartsHub(self.permissions)
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 

    def btn_Settings_click(self, **event_args):
        self.highlight_active_button("SETTINGS")
        ModNavigation.go_Settings(self.permissions)
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 

    def btn_Logout_click(self, **event_args):
        self.highlight_active_button("LOGOUT")
        open_form('LogoutBackground')
        anvil.users.logout()
        open_form("Launcher")

    def link_1_click(self, **event_args):
        """This method is called when the link is clicked"""
        alert(content=FAQ(), dismissible=False,large=True)

    #Avoid constant session refresh
    def timer_keepalive_tick(self, **event_args):
        """This method is called Every [interval] seconds. Does not trigger if [interval] is 0."""
        self.timer_keepalive.interval= 0
        result=anvil.server.call('fe_keepalive')
        if result == "ok":
            self.timer_keepalive.interval = 300

    def btn_ResetPassword_click(self, **event_args):
        """This method is called when the button is clicked"""
        anvil.users.change_password_with_form()
        
    def notification_timer_tick(self, **event_args):
        """This method is called Every [interval] seconds. Does not trigger if [interval] is 0."""

        # Call get_user() once to save local database checks
        user = anvil.users.get_user()
        if not user:
            return

        with anvil.server.no_loading_indicator:
            self.notification_label.text = ""

            # Make ONE server call to get all data
            data = anvil.server.call_s('fetch_all_dashboard_notifications', user)
            
            # Extract the lists from the returned dictionary
            notifications = data.get("notifications", [])
            incomplete_defects = data.get("incomplete_defects", [])
            tech_portal_info = data.get("technician_portal", [])
            pricing_alert = data.get("pricing_alert", [])
            
            # Simplify boolean logic (if list has items, bool() is True, else False)
            self.btn_alerts.enabled = bool(notifications)
            self.btn_IncompleteDefectsInfo.enabled = bool(incomplete_defects)
            self.btn_ViewTechnicianPortalDetails.enabled = bool(tech_portal_info)
            self.btn_ViewBuyingPriceExceedsSelling.enabled = bool(pricing_alert)

            # Handle the notification label text
            for n in notifications:
                self.notification_label.text = f"{n['jobcard']} - {n['message']}"
                self.refresh()

    def btn_alerts_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_alerts.enabled=False
        alert(content=Alerts(), dismissible=False,large=True)
        self.btn_alerts.enabled=True

    def btn_IncompleteDefectsInfo_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_IncompleteDefectsInfo.enabled=False
        alert(content=IncompleteDefectsInfo(), dismissible=False,large=True)
        self.btn_IncompleteDefectsInfo.enabled=True

    
    def btn_ViewTechnicianPortalDetails_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_ViewTechnicianPortalDetails.enabled=False
        alert(content=ViewTechnicianPortalDetails(), dismissible=False,large=True)
        self.btn_ViewTechnicianPortalDetails.enabled=True


    def btn_ViewBuyingPriceExceedsSelling_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_ViewBuyingPriceExceedsSelling.enabled=False
        alert(content=ViewPricingAlertDetails(), dismissible=False,large=True)
        self.btn_ViewBuyingPriceExceedsSelling.enabled=True

    

   