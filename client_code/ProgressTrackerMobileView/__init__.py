from ._anvil_designer import ProgressTrackerMobileViewTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from ..JobCardForm import JobCardForm
from ..DefectsForm import DefectsForm
from ..QuoteForm import QuoteForm
from ..InvoiceForm import InvoiceForm
from ..PaymentForm import PaymentForm
from ..ConfirmForm import ConfirmForm

class ProgressTrackerMobileView(ProgressTrackerMobileViewTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
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

    def btn_SearchCustomer_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        if self.txtJobCardRef.text:
            search_value = self.txtJobCardRef.text
            result = anvil.server.call("getJobCardDetailsWithRefOrFullnameSearch", search_value)
            # Clear drop down
            self.drop_down_JobCardRefDetails.items = ""

            self.drop_down_JobCardRefDetails.items = result
        else:
            alert(
                "Please enter job card ref to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtJobCardRef.focus()

    def drop_down_JobCardRefDetails_change(self, **event_args):
        """This method is called when an item is selected"""
        if self.drop_down_JobCardRefDetails.selected_value:
            result = anvil.server.call(
                "getJobCardRow", self.drop_down_JobCardRefDetails.selected_value
            )

            # Populate vehicle details
            self.label_MakeAndModel.text = result["MakeAndModel"]
            self.label_Mileage.text = result["Mileage"]
            self.label_RegNo.text = result["RegNo"]
            self.label_date_received.text = result["ReceivedDate"]

            # Populate vehicle owner details
            clientDetails = anvil.server.call(
                "getClientReport", result["ClientDetails"]
            )

            self.label_Owner.text = clientDetails[0]["Fullname"]
            self.label_Phone.text = clientDetails[0]["Phone"]

            # Populate payment details
            self.populatePaymentDetails(self.drop_down_JobCardRefDetails.selected_value)

            # Populate progress tracker
            if result["Status"] == "Ready for Pickup":
                invoice_status = anvil.server.call(
                    "getInvoiceStatus", self.drop_down_JobCardRefDetails.selected_value
                )
                self.set_progress_state(invoice_status)
            elif result["Status"] != "Ready for Pickup":
                self.set_progress_state(result["Status"])

        else:
            alert(
                "Please enter job card ref to procced.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.drop_down_JobCardRefDetails.focus()

    def set_progress_state(self, active_state):
        # Dictionary mapping states to label components
        status_labels = {
            "Checked In": self.label_checked_in,
            "Create Quote": self.label_create_quote,
            "Confirm Quote": self.label_confirm_quote,
            "In Service": self.label_in_service,
            "Verify Task": self.label_verify_task,
            "Issue Invoice": self.label_issue_invoice,
            "Cancelled Jobcard": self.label_cancelled,
            "Pending": self.label_payment_due,
            "Paid": self.label_payment_done,
        }

        # Loop over all labels and set styles
        for status, label in status_labels.items():
            if status == active_state:
                label.background = "black"
                label.foreground = "white"
            else:
                label.background = "white"
                label.foreground = "black"

        if active_state == "Cancelled Jobcard":
            self.text_area_1.text = anvil.server.call("getCancelledJobcardReason", self.drop_down_JobCardRefDetails.selected_value)
            self.text_area_1.visible = True
        else:
            self.text_area_1.visible=False
            
    def populatePaymentDetails(self, jobcardID, **event_args):
        invoice_status = anvil.server.call("getInvoiceStatus", jobcardID)
        self.label_Due.text = anvil.server.call(
            "get_invoice_total_by_job_id", jobcardID
        )
        self.label_Paid.text = anvil.server.call("get_previous_payment", jobcardID)

        if invoice_status == "Pending":
            if self.label_Paid.text == 0:
                self.label_Balance.text = self.label_Due.text
            else:
                bal = float(self.label_Due.text.replace(",", "")) - float(
                    self.label_Paid.text.replace(",", "")
                )
                self.label_Balance.text = f"{bal:,.2f}"

            self.label_Discount.text = (
                0  # Discount may be issued upon final balance payment
            )

        elif invoice_status == "Paid":
            bal = float(self.label_Due.text.replace(",", "")) - float(
                self.label_Paid.text.replace(",", "")
            )
            if bal > 0:  # Discount has been issued
                self.label_Discount.text = f"{bal:,.2f}"
                self.label_Balance.text = 0
        elif (
            self.label_Due.text == 0 and self.label_Paid.text == 0
        ):  # No invoice has been issued
            self.label_Discount.text = 0
            self.label_Balance.text = 0

    def btn_JobCard_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_JobCard.enabled = False
        job_id = self.drop_down_JobCardRefDetails.selected_value

        # Call the server first to check for data
        jobcard_data = anvil.server.call("getJobCardRow", job_id)

        if not jobcard_data:
            alert(
                "No data found for the selected Job ID.",
                title="Missing Job Card Data",
                large=False,
            )
            return

        # If data exists, now show the form and pass the quote_data along
        alert(
            content=JobCardForm(jobcard_data=jobcard_data),
            buttons=[],
            dismissible=False,
            large=True,
        )
        self.btn_JobCard.enabled = True

    def btn_Defects_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Defects.enabled = False
        job_id = self.drop_down_JobCardRefDetails.selected_value

        # Call the server first to check for data
        defects_data = anvil.server.call("getJobCardRef", job_id)

        if not defects_data:
            alert(
                "No data found for the selected Job ID.",
                title="Missing Defects Data",
                large=False,
            )
            return

        # If data exists, now show the form and pass the quote_data along
        alert(
            content=DefectsForm(defects_data=defects_data),
            buttons=[],
            dismissible=False,
            large=True,
        )
        self.btn_Defects.enabled = True

    def btn_Quotation_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Quotation.enabled = False
        job_id = self.drop_down_JobCardRefDetails.selected_value

        # Call the server first to check for data
        quote_data = anvil.server.call("get_quote_details_by_job_id", job_id)

        if not quote_data:
            alert(
                "No data found for the selected Job ID.",
                title="Missing Quotation Data",
                large=False,
            )
            return

        # If data exists, now show the form and pass the quote_data along
        alert(
            content=QuoteForm(job_id, quote_data=quote_data),
            buttons=[],
            dismissible=False,
            large=True,
        )
        self.btn_Quotation.enabled = True
        
    def btn_Confirmed_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Confirmed.enabled = False
        job_id = self.drop_down_JobCardRefDetails.selected_value

        # Call the server first to check for data
        quote_data = anvil.server.call("get_quote_confirmation_details_by_job_id", job_id)

        if not quote_data:
            alert("No data found for the selected Job ID.", title='Missing Quotation Data', large=False)
            return

        # If data exists, now show the form and pass the quote_data along
        alert(content=ConfirmForm(job_id, quote_data=quote_data), buttons=[], dismissible=False, large=True)
        self.btn_Confirmed.enabled = True
    def btn_Invoice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Invoice.enabled = False
        job_id = self.drop_down_JobCardRefDetails.selected_value

        # Call the server first to check for data
        quote_data = anvil.server.call("get_invoice_details_by_job_id", job_id)

        if not quote_data:
            alert(
                "No data found for the selected Job ID.",
                title="Missing Invoice Data",
                large=False,
            )
            return

        # If data exists, now show the form and pass the quote_data along
        alert(
            content=InvoiceForm(job_id, quote_data=quote_data),
            buttons=[],
            dismissible=False,
            large=True,
        )
        self.btn_Invoice.enabled = True
    def btn_Payment_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Payment.enabled = False
        job_id = self.drop_down_JobCardRefDetails.selected_value

        # Call the server first to check for data
        payment_data = anvil.server.call("getPaymentsDetails", job_id)

        if not payment_data:
            alert(
                "No data found for the selected Job ID.",
                title="Missing Payment Data",
                large=False,
            )
            return

        # If data exists, now show the form and pass the quote_data along
        alert(
            content=PaymentForm(job_id, payment_data=payment_data),
            buttons=[],
            dismissible=False,
            large=True,
        )
        self.btn_Payment.enabled = True