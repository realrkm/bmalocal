from ._anvil_designer import RowTemplate14Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
class RowTemplate14(RowTemplate14Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

    def _notify_parent_refresh(self):
        curr = self.parent
        while curr is not None:
            if hasattr(curr, "refresh_users"):
                curr.refresh_users(force_refresh=True)
                return
            curr = getattr(curr, "parent", None)

    def btn_Edit_click(self, **event_args):
        """Open EditUserAccounts with zero blocking server lookups."""
        from ...EditUserAccounts import EditUserAccounts
        outcome = alert(content=EditUserAccounts(self.item), buttons=[], dismissible=False, large=True)
        if outcome == "updated":
            self._notify_parent_refresh()

    def btn_ResetForgotPassword_click(self, **event_args):
        """Open ResetForgotPassword lazily."""
        from ...ResetForgotPassword import ResetForgotPassword
        alert(content=ResetForgotPassword(self.item), buttons=[], dismissible=False, large=True)

    