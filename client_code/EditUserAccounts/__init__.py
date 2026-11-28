from ._anvil_designer import EditUserAccountsTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModGetData


class EditUserAccounts(EditUserAccountsTemplate):
    def __init__(self, items, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        roles = ModGetData.getRolesCached() or []
        self.drop_down_role.items = roles

        self.label_oldemail.text = items["email"]
        self.txt_email.text = items["email"]

        role_id = items.get("role_id")
        if role_id is None and items.get("role"):
            role_id = next((val for label, val in roles if label == items["role"]), None)
            if role_id is None:
                role_id = anvil.server.call_s("get_role_id", items["role"])
        self.drop_down_role.selected_value = role_id

        self.drop_down_active.selected_value = items["enabled"]
        if "loginattempts" in items:
            self.text_box_login_attempts.text = items["loginattempts"]
        else:
            self.text_box_login_attempts.text = anvil.server.call_s("getFailedAttempts", items["email"])

    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        oldemail = self.label_oldemail.text
        email = self.txt_email.text.strip()
        role = self.drop_down_role.selected_value
        active = True if self.drop_down_active.selected_value == "Yes" else False

        # Validate inputs
        if not email:
            Notification("Email is required.", title="Error", style="danger", timeout=3).show()
            return
        if not role:
            Notification("Role is required.", title="Error", style="danger", timeout=3).show()
            return
        if active not in [True, False]:
            Notification("Active status is required.", title="Error", style="danger", timeout=3).show()
            return

        # Call server
        updated = False
        try:
            result = anvil.server.call("update_user", email=oldemail, new_email=email, enabled=active, role_id=role)
            updated = True
            alert(result, large=False)
        except Exception as e:
            alert(str(e), title="Error", large=False)
        self.raise_event("x-close-alert", value="updated" if updated else False)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=False)

