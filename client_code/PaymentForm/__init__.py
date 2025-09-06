from ._anvil_designer import PaymentFormTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class PaymentForm(PaymentFormTemplate):
    def __init__(self, jobcard_id, payment_data=None, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.refresh_client_table(payment_data)
        set_default_error_handling(self.handle_server_errors) #Set global server error handler
        
        self.label_JobCardID.text = jobcard_id
        
        if payment_data is not None:
            self.btn_download.visible = True
            self.image_1.visible = True
        else:
            self.btn_download.visible= False
            self.image_1.visible=False

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def refresh_client_table(self, payment_data):
        self.client_repeater.items = payment_data

    def btn_download_click(self, **event_args):
        """This method is called when the button is clicked"""
        jobCardID = self.label_JobCardID.text
        media_object = anvil.server.call('createReportPdf', jobCardID, "Payment")
        anvil.media.download(media_object)
        self.deleteFile(jobCardID, "Payment")
        self.btn_Close_click()
        
    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

