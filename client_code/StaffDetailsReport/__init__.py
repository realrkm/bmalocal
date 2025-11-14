from ._anvil_designer import StaffDetailsReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class StaffDetailsReport(StaffDetailsReportTemplate):
    def __init__(self, staffID, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.refresh_staff_table(staffID)
        set_default_error_handling(
            self.handle_server_errors
        )  # Set global server error handler

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert(
                "Connection to server lost. Please check your internet or try again later.",
                title="Disconnected",
                large=False,
            )
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert(
                "Please connect to the internet to proceed.",
                title="No Internet",
                large=False,
            )
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def refresh_staff_table(self, staffID):
        staffs = anvil.server.call("getStaffReport", staffID)
        self.client_repeater.items = staffs
