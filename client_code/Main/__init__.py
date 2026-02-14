from ._anvil_designer import MainTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import ModNavigation
import anvil.js
from anvil.js.window import navigator
from ..FAQ import FAQ
from ..Alerts import Alerts
from ..IncompleteDefectsInfo import IncompleteDefectsInfo
from ..ViewTechnicianPortalDetails import ViewTechnicianPortalDetails

class Main(MainTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        user = anvil.users.get_user()
        
        
        if user:
            # Fetch permissions from server
            self.permissions = anvil.server.call("get_user_permissions", user["role_id"])
            self.apply_permissions()

            if user['role_id']==1:
                self.refresh()
            else:
                self.notification_label.visible=False
                self.btn_alerts.visible=False
                self.btn_IncompleteDefectsInfo.visible=False
            user_agent = navigator.userAgent
            # Now call your server function and pass the user_agent
            anvil.server.call_s('get_stats', user_agent)

            ModNavigation.home_form = self
                

        
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

            # Simplify boolean logic (if list has items, bool() is True, else False)
            self.btn_alerts.enabled = bool(notifications)
            self.btn_IncompleteDefectsInfo.enabled = bool(incomplete_defects)
            self.btn_ViewTechnicianPortalDetails.enabled = bool(tech_portal_info)

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

    