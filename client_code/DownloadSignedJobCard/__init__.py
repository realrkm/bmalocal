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
        
    def btn_SearchRegNo_click(self, **event_args):
        """This method is called when the button is clicked"""
        jobCardRef = self.txt_JobcardRef.text
        items = anvil.server.call("getCheckedInJobcards", jobCardRef)
        self.cmbJobCardID.items = items


    def btn_DownloadJobCard_click(self, **event_args):
        """Triggered when user clicks 'Download JobCcard' button in Anvil UI"""
        self.btn_DownloadJobCard.enabled = False #Prevent multiple clicks 

        if not self.cmbJobCardID.selected_value:
            alert("Sorry, please select job card ref to proceed.", title="Blank Field(s) Found", large=False)
            self.cmbJobCardID.focus()
            self.btn_DownloadJobCard.enabled = True
            return

        if not self.signature_form_1.get_signature_image():
            alert("Sorry, please sign job card ref to proceed.", title="Missing Signature", large=False)
            self.btn_DownloadJobCard.enabled = True
            return

        jobCardID = self.cmbJobCardID.selected_value
        signature = self.signature_form_1.get_signature_image()
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

    