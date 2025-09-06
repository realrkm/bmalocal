from ._anvil_designer import QuoteFormTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class QuoteForm(QuoteFormTemplate):
    def __init__(self, job_id, quote_data=None, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.label_JobCardID.text = job_id
        set_default_error_handling(self.handle_server_errors)
        jobcardref = anvil.server.call_s("getJobCardRef", job_id)
        
        if jobcardref[0]['JobCardRef'].split("-")[-1] == "IQ":
            self.label_2.text = "INTERIM QUOTATION"
            is_interim = True
        else:
            is_interim = False
            
        if quote_data:
            # Set form fields using the first row (all other rows are assumed to have same metadata)
            first_row = quote_data[0]
            self.txtCustomerName.text = first_row["Fullname"]
            self.txtMakeAndModel.text = first_row["MakeAndModel"]
            self.txtRegNo.text = first_row["RegNo"]
            self.txtDate.text = str(first_row["Date"])
            self.txtChassis.text = first_row["ChassisNo"]
            self.txtEngine.text = first_row["EngineCode"]
            self.txtMileage.text = first_row["Mileage"]

            # Set DataGrid rows
            items_for_grid = [
                {
                    "Item": row["Item"],
                    "Quantity": row["QuantityIssued"],
                    "Amount": (
                        "TO BE CONFIRMED"
                        if is_interim and float(str(row['Amount']).replace(',', '').strip() or "0") == 0
                        else f"{float(str(row['Amount']).replace(',', '').strip()):,.2f}"
                    ),
                    "Total": (
                        "TO BE CONFIRMED"
                        if is_interim and float(str(row['Total']).replace(',', '').strip() or "0") == 0
                        else f"{float(str(row['Total']).replace(',', '').strip()):,.2f}"
                    )
                } for row in quote_data
                ]

            self.repeating_panel_1.items = items_for_grid
              
            # Call total calculator
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
        grandTotal = sum(
            float(item['Total'].replace(',', '')) if str(item['Total']).replace(',', '').replace('.', '').isdigit()
            else 0
            for item in self.repeating_panel_1.items
        )
        self.txtTotal.text = f"Grand Total  {grandTotal:,.2f}                     "  # Format with 2 decimals and add spaces
        
    def button_1_click(self, **event_args):
        """This method is called when the button is clicked"""
        jobCardID = self.label_JobCardID.text
        
        if self.label_2.text == "INTERIM QUOTATION":
            media_object = anvil.server.call('createQuotationInvoicePdf', jobCardID, "InterimQuotation")
        else:
            media_object = anvil.server.call('createQuotationInvoicePdf', jobCardID, "Quotation")
            
        anvil.media.download(media_object)
        
        if self.label_2.text == "INTERIM QUOTATION":
            self.deleteFile(jobCardID, "InterimQuotation")
        else:
            self.deleteFile(jobCardID, "Quotation")
        self.btn_Close_click()

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

   