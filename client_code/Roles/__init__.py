from ._anvil_designer import RolesTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class Roles(RolesTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.repeating_panel_1.items = anvil.server.call("listRoles")

    def btn_AddRole_click(self, **event_args):
        """This method is called when the button is clicked"""
        role = self.txtRole.text.strip()
        description = self.txtDescription.text.strip()
    
        if not role or not description:
            alert("Sorry, please enter both role and description to proceed.", 
                title="Blank Field(s) Found", large=False)
            self.txtRole.focus()
            return
    
        result = anvil.server.call("duplicateRole", role, description)
    
        if result["status"] == "duplicate":
            alert(f"Role '{result['role']}' already exists with description: {result['description']}",
                title="Duplicate Role", large=False)
        elif result["status"] == "inserted":
            alert(f"Role '{result['role']}' added successfully!",
                title="Success", large=False)
    
        # Refresh role list
        self.repeating_panel_1.items = anvil.server.call("listRoles")

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
