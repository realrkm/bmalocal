from ._anvil_designer import LauncherTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
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
                # Now call your server function and pass the user_agent
                anvil.server.call_s('get_stats', user_agent)
                return
            else:
                open_form("Main", permissions=self.permissions, user=user)
        
