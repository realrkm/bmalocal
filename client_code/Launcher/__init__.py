from ._anvil_designer import LauncherTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from anvil.js.window import navigator

class Launcher(LauncherTemplate):
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
            if self.permissions['TECHNICIAN PORTAL']['main']:
                open_form('SelfService')
                user_agent = navigator.userAgent
                # Defer analytics call so it does not block the form transition
                anvil.js.window.setTimeout(lambda: anvil.server.call_s('get_stats', user_agent), 4000)
                return
            else:
                open_form("Main", permissions=self.permissions, user=user)
        
