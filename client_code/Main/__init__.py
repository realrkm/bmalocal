from ._anvil_designer import MainTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
from .. import ModNavigation
from .. import ModGetData
import anvil.js
from anvil.js import window
from anvil.js.window import navigator, setTimeout
from ..NotificationsAndAlerts import NotificationsAndAlerts
from ..WalkieTalkieChat import WalkieTalkieChat

class Main(MainTemplate):

    def __init__(self, permissions=None, user=None, **properties):
        self.init_components(**properties)
        self.home_component = self.column_panel_content
        anvil.js.call('replaceBanner')
    
        self.user = user
        if self.user is None:
            while anvil.users.get_user() is None:
                anvil.users.login_with_form()
            self.user = anvil.users.get_user()
    
        if self.user:
            self.permissions = permissions or anvil.server.call("get_user_permissions", self.user["role_id"])
            self.apply_permissions()
    
            if self.user['role_id'] == 1:
                self.refresh()
            else:
                self.notification_label.visible = False
                self.error_label.visible = False
                self.notificationsandalerts = None
    
            user_agent = navigator.userAgent
            anvil.js.window.setTimeout(lambda: anvil.server.call_s('get_stats', user_agent), 0)
    
            ModNavigation.home_form = self
            self.error_label.visible = False
    
            set_default_error_handling(
                lambda exc: ModGetData.handle_server_errors(exc, self.error_label)
            )
    
            self.polling_active = True
            self.poll_running = False   # ← new guard
            self.timeout_id = None
            anvil.js.window.setTimeout(self.start_notification_loop, 0)
    
        # Initialize Walkie Talkie Real-Time Chat
        self.live_popup.clear()
        user_prof = None
        if self.user:
            try:
                email = self.user["email"] if "email" in self.user else ""
                role_id = self.user["role_id"] if "role_id" in self.user else None
                if email:
                    user_prof = {
                        "email": email,
                        "name": email.split("@")[0],
                        "role_name": "Admin" if role_id == 1 else "Staff",
                    }
            except Exception:
                pass
        self.walkie_chat = WalkieTalkieChat(user_profile=user_prof, on_close=self.close_chat)
        self.live_popup.add_component(self.walkie_chat, full_width_row=True)

        self.live_popup.visible = False
        self.fab_btn.tooltip = "Walkie Talkie Chat"
        self.fab_btn.enabled = True
        self.is_open = False
        self._safe_js_call("setWtChatOpenStatus", False)
        self._safe_js_call("updateWtBadgeDisplay")

    def _safe_js_call(self, fn_name, *args):
        """Invoke a JS function on window safely without throwing if not yet ready."""
        try:
            fn = getattr(anvil.js.window, fn_name, None)
            if callable(fn):
                fn(*args)
            else:
                anvil.js.call(fn_name, *args)
        except Exception:
            pass

    def close_chat(self):
        """Close the Walkie Talkie chat popup window."""
        self.live_popup.visible = False
        self.is_open = False
        self._safe_js_call("setWtChatOpenStatus", False)

    def start_notification_loop(self):
        self.polling_active=True
        self.run_notification_poll()

    def run_notification_poll(self, *args):
        """The core polling block — guarded against stacking."""
        if not self.polling_active or self.poll_running:
            return
    
        self.poll_running = True
        try:
            with anvil.server.no_loading_indicator:
                self.notification_label.text = ""
                self.notificationsandalerts = anvil.server.call_s(
                    'fetch_all_dashboard_notifications', self.user
                )
                data = self.notificationsandalerts
    
                notifications = data.get("notifications", [])
                incomplete_defects = data.get("incomplete_defects", [])
                tech_portal_info = data.get("technician_portal", [])
                pricing_alert = data.get("pricing_alert", [])
    
                notice = sum([bool(notifications), bool(incomplete_defects), bool(tech_portal_info), bool(pricing_alert)])
    
                if notice > 0:
                    self.link_1.visible = True
                    self.link_1.text = str(notice)
                    self.link_1.foreground = "#00FF00"
                else:
                    self.link_1.visible = False
                    self.link_1.text = None
                    self.link_1.foreground = "#FFFFFF"
    
                for n in notifications:
                    self.notification_label.text = f"{n['jobcard']} - {n['message']}"
                    self.refresh()
    
        except Exception as e:
            if "Authentication" in str(e) or "auth" in str(e).lower():
                self.polling_active = False
                self.timeout_id = None
                return
            print(f"Notification poll failed temporarily: {e}")
        finally:
            self.poll_running = False   # ← releases the guard
            if self.polling_active:
                self.timeout_id = anvil.js.window.setTimeout(self.run_notification_poll, 5000)

    def link_1_click(self, **event_args):
        """This method is called when the alert link is clicked"""
        result = alert(content=NotificationsAndAlerts(self.user), title="Notifications And Alerts", dismissible=False, large=False)
        if result:
            # Instead of recursively calling a tick, we manually fire one iteration instantly
            self.run_notification_poll()
            
    # ─────────────────────────────────────────────
    # FAB CLICK: Display / Hide Chat Window
    # ─────────────────────────────────────────────

    def fab_btn_click(self, **event_args):
        if self.is_open:
            self.close_chat()
        else:
            self.live_popup.visible = True
            self.is_open = True
            self._safe_js_call("setWtChatOpenStatus", True)
            self._safe_js_call("clearWtUnreadCount")
            self._safe_js_call("scrollWtChatToBottom")
            try:
                anvil.js.window.setTimeout(
                    lambda: (
                        self._safe_js_call("scrollWtChatToBottom"),
                        anvil.js.window.document.getElementById("wtInputMessage")
                        and anvil.js.window.document.getElementById("wtInputMessage").focus()
                    ),
                    120,
                )
            except Exception:
                pass
        
            
    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def apply_permissions(self):
        """Apply user permissions to the sidebar only"""
        section_map = {
            "CONTACT": self.btn_Contact,
            "JOB CARD": self.btn_JobCard,
            "BOOKING": self.btn_Booking,
            "WORKFLOW": self.btn_Workflow,
            "TRACKER": self.btn_Tracker,
            "REVISION": self.btn_Revision,
            "PAYMENT": self.btn_Payment,
            "INVENTORY": self.btn_Inventory,
            "REPORTS": self.btn_Report,
            "PARTS HUB": self.btn_PartsHub,
            "SETTINGS": self.btn_Settings,
            "RESET": self.btn_ResetPassword,
            "FAQs":self.btn_FAQs,
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
        self.column_panel_main.clear()
        self.column_panel_main.add_component(cmpt, full_width_row=True)
        # Ensure floating chat button and chat popup remain visible across all pages
        if self.fab_btn not in self.column_panel_main.get_components():
            self.column_panel_main.add_component(self.fab_btn)
        if self.live_popup not in self.column_panel_main.get_components():
            self.column_panel_main.add_component(self.live_popup)
        self.live_popup.visible = self.is_open
        # Now refresh the page
        self.refresh_data_bindings()
        self._safe_js_call("updateWtBadgeDisplay")
        if self.is_open:
            self._safe_js_call("scrollWtChatToBottom")
        
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
     
    def btn_Booking_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("BOOKING")
        ModNavigation.go_Booking()
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
        
    def btn_ResetPassword_click(self, **event_args):
        """This method is called when the button is clicked"""
        anvil.users.change_password_with_form()

    def btn_FAQs_click(self, **event_args):
        self.highlight_active_button("FAQs")
        ModNavigation.go_FAQs()
        #Now hide sidebar after clicking link. 
        #Additional function in standard-page.html
        self.call_js('hideSidebarIfModal') 
        
    def btn_Logout_click(self, **event_args):
        # Stop the poll first, before anything else
        self.polling_active = False
        if self.timeout_id is not None:
            anvil.js.window.clearTimeout(self.timeout_id)
            self.timeout_id = None
        self.user = None  # Clear the user reference immediately

        # Explicitly disconnect Walkie Talkie chat on logout
        self._safe_js_call("disconnectWtChat")

        self.highlight_active_button("LOGOUT")
        open_form('LogoutBackground')
        anvil.users.logout()
        open_form("Launcher")    

    def form_show(self, **events_args):
        """Optional: Ensure polling restarts if the form is re-shown"""
        if not self.polling_active:
            self.start_notification_loop()
        self._safe_js_call("updateWtBadgeDisplay")

    def form_hide(self, **events_args):
        self.polling_active = False
        if self.timeout_id is not None:
            anvil.js.window.clearTimeout(self.timeout_id)  # ← lowercase 't', was clearTimeOut
            self.timeout_id = None

   
    