from ._anvil_designer import UserAccountsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData
from .. import ModCache


class UserAccounts(UserAccountsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        self.set_event_handler("show", self._on_form_show)

        cached = ModCache.get_cached("users_list")
        if cached is not None:
            self.repeating_panel_1.items = cached
        else:
            try:
                anvil.js.window.setTimeout(lambda: self.refresh_users(force_refresh=False), 0)
            except Exception:
                self.refresh_users(force_refresh=False)

    def refresh_users(self, force_refresh=False):
        try:
            with anvil.server.no_loading_indicator:
                if not force_refresh and ModCache.get_cached("users_list") is None:
                    ModGetData.warmSettingsCaches()
                rows = ModGetData.getUsersCached(force_refresh=force_refresh)
            self.repeating_panel_1.items = rows or []
        except Exception:
            pass

    def _on_form_show(self, **event_args):
        cached = ModCache.get_cached("users_list")
        if cached is not None and self.repeating_panel_1.items != cached:
            self.repeating_panel_1.items = cached
      