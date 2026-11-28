from ._anvil_designer import RolesTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


class Roles(RolesTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        self._updated = False
        with anvil.server.no_loading_indicator:
            self.repeating_panel_1.items = ModGetData.getRolesListCached() or []

    def btn_AddRole_click(self, **event_args):
        """This method is called when the button is clicked"""
        role = self.txtRole.text.strip()
        description = self.txtDescription.text.strip()

        if not role or not description:
            Notification("Sorry, please enter both role and description to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtRole.focus()
            return

        result = anvil.server.call("duplicateRole", role, description)

        if result["status"] == "duplicate":
            alert(
                f"Role '{result['role']}' already exists with description: {result['description']}",
                title="Duplicate Role",
                large=False,
            )
        elif result["status"] == "inserted":
            self._updated = True
            alert(f"Role '{result['role']}' added successfully!", title="Success", large=False)
            self.repeating_panel_1.items = ModGetData.getRolesListCached(force_refresh=True) or []
            self.txtRole.text = ""
            self.txtDescription.text = ""

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value="updated" if self._updated else False)
