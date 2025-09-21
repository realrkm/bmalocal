from ._anvil_designer import DownloadSignedJobCardTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.js.window import window
import anvil.js
import base64
import time
from datetime import datetime


class DownloadSignedJobCard(DownloadSignedJobCardTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors) #Set global server error handler

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)   
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def btn_SearchRegNo_click(self, **event_args):
        """This method is called when the button is clicked"""
        jobCardRef = self.txt_JobcardRef.text
        items = anvil.server.call("getCheckedInJobcards", jobCardRef)
        self.cmbJobCardID.items = items


    def get_signature_image(self):
        # Wait a short time to ensure JS function is available
        for _ in range(20):  # Retry for up to 1 seconds
            if hasattr(window, "getSignatureData"):
                break
            time.sleep(0.5)
        else:
            alert("Signature pad is not ready. Please try again in a moment.")
            return

        # Call the JavaScript function
        data_url = window.getSignatureData()

        if not data_url:
            alert("No signature was captured. Please draw a signature first.")
            return

        # Split data URL to get the base64 content
        header, encoded = data_url.split(",", 1)
        binary_data = base64.b64decode(encoded)

        # Create an Anvil Media object
        media = BlobMedia("image/png", binary_data, name="signature.png")

        # Return or store the media for further use
        return media

    def btn_DownloadJobCard_click(self, **event_args):
        """Triggered when user clicks 'Download JobCcard' button in Anvil UI"""
        self.btn_DownloadJobCard.enabled = False #Prevent multiple clicks 

        if not self.cmbJobCardID.selected_value:
            alert("Sorry, please select job card ref to proceed.", title="Blank Field(s) Found", large=False)
            self.cmbJobCardID.focus()
            self.btn_DownloadJobCard.enabled = True
            return

        if not self.get_signature_image():
            self.btn_DownloadJobCard.enabled = True
            return

        jobCardID = self.cmbJobCardID.selected_value
        signature = self.get_signature_image()
        createdAt = datetime.now()
        
        anvil.server.call('saveSignedJobCardDetails', jobCardID, signature, createdAt) 
        anvil.server.call_s('fillJobCardReport',jobCardID)
        alert("Signed jobcard saved successfully and download is initiated.", title="Success")
        self.downloadJobcardPdf(jobCardID)

        # Close Form
        self.btn_Close_click()
       
    def downloadJobcardPdf(self, jobCardID):
        media_object = anvil.server.call('createSignedJobcardPdf', jobCardID)
        anvil.media.download(media_object)
        self.deleteFile(jobCardID, "Jobcard")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)

    