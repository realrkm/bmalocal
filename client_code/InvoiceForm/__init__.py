from ._anvil_designer import InvoiceFormTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class InvoiceForm(InvoiceFormTemplate):
    def __init__(self, job_id, quote_data=None, **properties):
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        self.label_JobCardID.text = job_id
        
        # Use provided data (already checked in caller)
        if quote_data:
            first_row = quote_data[0]
            self.txtCustomerName.text = first_row["Fullname"]
            self.txtMakeAndModel.text = first_row["MakeAndModel"]
            self.txtRegNo.text = first_row["RegNo"]
            self.txtDate.text = str(first_row["Date"])
            self.txtChassis.text = first_row["ChassisNo"]
            self.txtEngine.text = first_row["EngineCode"]
            self.txtMileage.text = first_row["Mileage"]

            self.repeating_panel_1.items = [
                {
                    "Item": row["Item"],
                    "Quantity": row["QuantityIssued"],
                    "Amount": f"{float(str(row['Amount']).replace(',', '')):,.2f}",
                    "Total":  f"{float(str(row['Total']).replace(',', '')):,.2f}"
                } for row in quote_data
            ]

            self.calculate_total_amount()

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
            
    def calculate_total_amount(self):
        grandTotal = sum(float(item['Total'].replace(',', '')) for item in self.repeating_panel_1.items)
        self.txtTotal.text = f"Grand Total  {grandTotal:,.2f}                     "  # Format with 2 decimals and add spaces
        
    def button_1_click(self, **event_args):
        """This method is called when the button is clicked"""
        jobCardID = self.label_JobCardID.text
        media_object = anvil.server.call('createQuotationInvoicePdf', jobCardID, "Invoice")
        anvil.media.download(media_object)
        self.deleteFile(jobCardID, "Invoice")
        self.btn_Close_click()

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
