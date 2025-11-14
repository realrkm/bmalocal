from ._anvil_designer import PaymentTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..PaidPendingInvoices import PaidPendingInvoices
import anvil.js


class Payment(PaymentTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors) #Set global server error handler

        #Set focus into technician
        self.search_keyword_1.text_box_search.focus()

        # Attach the event that fetches Invoices
        self.search_keyword_1.set_event_handler('x-get-search-keys', self.getInvoices)
        self.search_keyword_1.text_box_search.placeholder = "Enter Invoice Job Card Ref"

        # Handle what happens when a user selects a result
        self.search_keyword_1.set_event_handler('x-search-hints-result', self.populatePaymentDetails)

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)   
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)
    
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        if self.start_date.date is None:
            alert("Enter start date to proceed", title="Blank Field Found", large=False)
            self.start_date.focus()
            return
                
        if self.end_date.date is None:
            alert("Enter end date to proceed", title="Blank Field Found", large=False)
            self.end_date.focus()
            return
    
        if self.end_date.date < self.start_date.date:
            alert("To proceed, ensure end date is be greater or equal to start date", title="Date Mismatch Found", large=False)
            self.start_date.focus()
            self.start_date.date =""
            self.end_date.date=""
            return
                
        if self.end_date.date >= self.start_date.date:
            start = self.start_date.date
            end = self.end_date.date
                
            summary = anvil.server.call('get_invoice_totals_and_counts_by_date', start, end)
                
            self.button_Paid.text = f"Fully Paid: {summary['Paid']['count']} invoice(s), Total {summary['Paid']['total']:,.2f} KSHS"
            self.button_Pending.text = f"Pending: {summary['Pending']['count']} invoice(s), Total {summary['Pending']['total']:,.2f} KSHS"

    def button_Paid_click(self, **event_args):
        """This method is called when the link is clicked"""
        if self.start_date.date is None or self.end_date.date is None:
            alert("Ensure start date is greater or equal to end date", title="Check Dates", large=False)
        elif self.button_Paid.text == "Paid: 0.0 KSHS ":
            alert("Click Search button after entering the dates", title="Click Search Button", large=False)
        elif self.start_date.date is not None and self.end_date.date is not None:
            alert(
                content=PaidPendingInvoices("Paid", self.start_date.date, self.end_date.date),
                buttons=[],
                title = "Paid Invoices",
                dismissible=True,
                large=True
            )
        

    def button_Pending_click(self, **event_args):
        """This method is called when the link is clicked"""
        if self.start_date.date is None or self.end_date.date is None:
            alert("Ensure start date is greater or equal to end date", title="Check Dates", large=False)
        elif self.button_Paid.text == "Pending: 0.0 KSHS":
            alert("Click Search button after entering the dates", title="Click Search Button", large=False)
        elif self.start_date.date is not None and self.end_date.date is not None:
            alert(
                content=PaidPendingInvoices("Pending", self.start_date.date, self.end_date.date),
                buttons=[],
                title = "Pending Invoices",
                dismissible=True,
                large=True
            )
        else:
            alert("Ensure start date is greater or equal to end date", title="Check Dates", large=False)
            
    def getInvoices(self,  **event_args):
        """Return invoice records to SearchKeyword."""
        results = anvil.server.call("getPendingInvoices")
        return [{'entry': r['JobCardRef'], 'ID': r['ID']} for r in results]

    def populatePaymentDetails(self, result, **event_args):
        """Do something when a result is selected from search hints."""
        jobcardID = result['ID']
        self.txt_InvoicedAmount.text = anvil.server.call_s('get_invoice_total_by_job_id', jobcardID) 
        self.text_box_PreviousPayment.text = anvil.server.call_s('get_previous_payment', jobcardID)
        bal = float(self.txt_InvoicedAmount.text.replace(",", "")) - float(self.text_box_PreviousPayment.text.replace(",", ""))
        self.text_box_Bal.text = bal
        
    def recalculate_balance(self):
    # Parse values safely
        invoiced = float(self.txt_InvoicedAmount.text.replace(",", "") or 0)
        previous = float(self.text_box_PreviousPayment.text.replace(",", "") or 0)
        discount = float(self.text_box_Discount.text or 0)
        paid = float(self.text_box_Amount.text or 0)
    
        # Calculate balance
        balance = invoiced - previous - paid - discount
    
        # Display and format balance
        self.text_box_Bal.text = f"{balance:.2f}"
    
        # Turn text red if negative, black if not
        if balance < 0:
            self.text_box_Bal.foreground = "red"
        else:
            self.text_box_Bal.foreground = "black"

    def text_box_Discount_change(self, **event_args):
        self.recalculate_balance()

    def text_box_Amount_change(self, **event_args):
        self.recalculate_balance()
        
    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_SaveAndNew.enabled = False
        
        if self.search_keyword_1.selected_result is None:
            alert("Enter Invoice Job Card Ref to proceed", title="Blank Field Found", large=False)
            self.btn_SaveAndNew.enabled = True
            self.search_keyword_1.text_box_search.focus()
            return
            
        if self.date_picker_1.date is None:
            alert("Enter Date to proceed", title="Blank Field Found", large=False)
            self.btn_SaveAndNew.enabled = True
            self.date_picker_1.focus()
            return

        if self.text_box_Amount.text is None:
            alert("Enter amount paid to proceed", title="Blank Field Found", large=False)
            self.btn_SaveAndNew.enabled = True
            self.text_box_Amount.focus()
            return

        if not self.text_box_PaymentMode.text.strip():
            alert("Enter payment mode details to proceed", title="Blank Field Found", large=False)
            self.btn_SaveAndNew.enabled = True
            self.text_box_PaymentMode.focus()
            return
            
        paymentDate = self.date_picker_1.date
        jobCardRefID = self.search_keyword_1.selected_result['ID']
        paymentMode = self.text_box_PaymentMode.text
        amountPaid = self.text_box_Amount.text
        discount = self.text_box_Discount.text
        bal = self.text_box_Bal.text

                  
        #Save Data
        anvil.server.call('save_payment_details', paymentDate, jobCardRefID, paymentMode, amountPaid, discount, bal)
        
        if bal <= 0:
            anvil.server.call_s("update_invoice_status", self.search_keyword_1.selected_result['ID'])
            
        alert('Payment saved successfully', title="Success", large=False)

        #Reload page
        get_open_form().btn_Payment_click()

    

   



    