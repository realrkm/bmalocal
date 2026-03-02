from ._anvil_designer import SelfServiceTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
import base64

class SelfService(SelfServiceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')       
        set_default_error_handling(self.handle_server_errors) #Set global server error handler

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            self._show_notification(
                message="Connection to server lost. Please check your internet or try again later.",
                title="Disconnected",
                style="danger"
            )
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            self._show_notification(
                message="Please connect to the internet to proceed.",
                title="No Internet",
                style="warning"
            )
        else:
            self._show_notification(
                message=f"Unexpected error: {exc}",
                title="Error",
                style="danger"
            )

    def _show_notification(self, message, title="", style="danger", timeout=3):
        """
        Displays an Anvil Notification that auto-dismisses after `timeout` seconds.
    
        :param message: The notification body text.
        :param title:   The notification title.
        :param style:   'danger' | 'warning' | 'success' | 'info'
        :param timeout: Seconds before the notification disappears (default: 3).
        """
        notif = Notification(
            message,
            title=title,
            style=style,      # controls the colour — danger=red, warning=orange, success=green, info=blue
            timeout=timeout,  # auto-dismisses after this many seconds
        )
        notif.show()

    def getCarPartNamesAndCategory(self):
        return anvil.server.call('getCarPartNamesAndCategory')

    def get_technician_jobcards_by_status(self):
        return anvil.server.call("get_technician_jobcards_by_status")

    def get_technicians_list(self):
        return anvil.server.call_s('get_technicians_list')
        
    def save_work_done(self, jobcardref, workdone):
        anvil.server.call("save_work_done_by_technician", jobcardref, workdone)
        return None

    def storeTechDetails(self, jobcard_ref, tech_notes, defects, parts, technician, signature_data):
        signature = self.get_signature_image(signature_data)
        JobCardID = anvil.server.call_s("getJobCardID", jobcard_ref)
        if parts is None:
            parts = "None"
        anvil.server.call('saveOrUpdateTechnicianPortalDefectsAndRequestedParts', JobCardID, tech_notes, defects, parts, technician, signature)
        return None

    def get_signature_image(self, signature_data):
        
        data_url = signature_data

        # Split data URL to get the base64 content
        header, encoded = data_url.split(",", 1)
        binary_data = base64.b64decode(encoded)

        # Create an Anvil Media object
        media = BlobMedia("image/png", binary_data, name="signature.png")

        # Return or store the media for further use
        return media

    def get_jobcard_and_defect_details(self, jobcardref):
        return anvil.server.call("get_jobcard_and_defect_details", jobcardref)

    def getCustomerFeedback(self, jobcardref):
        return anvil.server.call("get_parts_and_feedback_by_jobcardref", jobcardref)

    def logoutUser(self):
        open_form('LogoutBackground')
        anvil.users.logout()