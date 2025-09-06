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
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
            
        self.label_JobCardID.text = job_id
        set_default_error_handling(self.handle_server_errors)

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



    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)   
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)
            
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
