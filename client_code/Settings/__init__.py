from ._anvil_designer import SettingsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..UserAccounts import UserAccounts
from ..UserRolesAndPermissions import UserRolesAndPermissions
import anvil.js 

class Settings(SettingsTemplate):
    def __init__(self, permissions, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.permissions = permissions

        # Apply permissions to buttons and load the first available subform
        self.apply_permissions()

    def apply_permissions(self):
        """Apply only SETTINGS-related permissions and load the first available subform."""
        settings_perms = self.permissions.get("SETTINGS", {"main": False, "subs": {}})

        first_visible = None  # track which subform to load first

        for subsection, value in settings_perms["subs"].items():
            if subsection == "User Accounts":
                self.btn_AddUser.visible = value
                self.btn_AddUser.enabled = value
                if value and first_visible is None:
                    first_visible = "USER ACCOUNT"

            elif subsection == "Roles And Permissions":
                self.btn_UserRoles.visible = value
                self.btn_UserRoles.enabled = value
                if value and first_visible is None:
                    first_visible = "ROLES AND PERMISSIONS"

        # Load the first visible subform automatically
        if first_visible:
            self.show_clicked_button(first_visible)

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
        self.highlight_active_button("USER ACCOUNT")
        self.card_2.visible=True
        self.card_2.clear()
        self.card_2.add_component(UserAccounts())
        self.btn_AddUser.background = "#000000"

    def btn_UserRoles_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("ROLES AND PERMISSIONS")
        self.card_2.visible=True
        self.card_2.clear()
        self.card_2.add_component(UserRolesAndPermissions())
        self.btn_UserRoles.background = "#000000"
       
   