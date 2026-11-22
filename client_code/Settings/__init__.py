from ._anvil_designer import SettingsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js 

class Settings(SettingsTemplate):
    def __init__(self, permissions, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self.permissions = permissions
        self._initial_subform_loaded = False
        self._first_visible = None

        # Apply permissions to buttons and defer first subform load to form_show
        self.apply_permissions()
        self.set_event_handler("show", self.form_show)

    def form_show(self, **event_args):
        """Load the first authorized subform once the Settings container is mounted."""
        if not self._initial_subform_loaded:
            self._initial_subform_loaded = True
            if self._first_visible:
                self.show_clicked_button(self._first_visible)

    def apply_permissions(self):
        """Apply only SETTINGS-related permissions and record the first available subform."""
        settings_perms = self.permissions.get("SETTINGS", {"main": False, "subs": {}})

        for subsection, value in settings_perms["subs"].items():
            if subsection == "User Accounts":
                self.btn_AddUser.visible = value
                self.btn_AddUser.enabled = value
                if value and self._first_visible is None:
                    self._first_visible = "USER ACCOUNT"

            elif subsection == "Roles And Permissions":
                self.btn_UserRoles.visible = value
                self.btn_UserRoles.enabled = value
                if value and self._first_visible is None:
                    self._first_visible = "ROLES AND PERMISSIONS"

    #This function is called when Contact form loads or when Save And New button is clicked in the forms loaded in card_2 component
    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "USER ACCOUNT":
            self.btn_AddUser_click()
        elif buttonName == "ROLES AND PERMISSIONS":
            self.btn_UserRoles_click()
        
    def highlight_active_button(self, selected_text):
        # Loop through all buttons in the panel
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"  # Highlighted black
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"  # Normal blue
                    comp.foreground = "white"
       
    def btn_AddUser_click(self, **event_args):
        """This method is called when the button is clicked"""
        from ..UserAccounts import UserAccounts
        self.highlight_active_button("USER ACCOUNT")
        self.card_2.visible=True
        self.card_2.clear()
        self.card_2.add_component(UserAccounts(), full_width_row=True)
        self.btn_AddUser.background = "#000000"

    def btn_UserRoles_click(self, **event_args):
        """This method is called when the button is clicked"""
        from ..UserRolesAndPermissions import UserRolesAndPermissions
        self.highlight_active_button("ROLES AND PERMISSIONS")
        self.card_2.visible=True
        self.card_2.clear()
        self.card_2.add_component(UserRolesAndPermissions(), full_width_row=True)
        self.btn_UserRoles.background = "#000000"
       
   