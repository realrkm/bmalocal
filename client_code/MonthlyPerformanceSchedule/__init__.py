from ._anvil_designer import MonthlyPerformanceScheduleTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..ViewSchedule import ViewSchedule
import anvil.js

class MonthlyPerformanceSchedule(MonthlyPerformanceScheduleTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        
    def searchInvoices(self, **event_args):
        """This method is called when the button is clicked"""
        startDate = self.date_picker_start.date
        endDate = self.date_picker_end.date
        
        if startDate and endDate is None:
            pass #Do nothing
        elif startDate is None and endDate is None:
            alert("Sorry, please enter date period to proceed", title="Blank Field(s) Found")
            return
        elif startDate is None and endDate:
            alert("Sorry, please enter start date to proceed", title="Blank Field(s) Found")
            return
        elif startDate > endDate:
            alert("Sorry, start date cannot be greater than end date", title="Mismatch Dates")
            return
        else:
            self.drop_down_1.items = anvil.server.call("getMonthlyJobcardRef", startDate, endDate)

    def drop_down_1_change(self, **event_args):
        """This method is called when an item is selected"""
        startDate = self.date_picker_start.date
        endDate = self.date_picker_end.date
        jobcardrefID = self.drop_down_1.selected_value
        
        if startDate is None and endDate is None:
            alert("Sorry, please enter date period to proceed", title="Blank Field(s) Found")
            return
        elif startDate is None and endDate:
            alert("Sorry, please enter start date to proceed", title="Blank Field(s) Found")
            return
        elif startDate > endDate:
            alert("Sorry, start date cannot be greater than end date", title="Mismatch Dates")
            return
        else:
            self.repeating_panel_1.items = anvil.server.call("getPeriodicInvoices", startDate, endDate, jobcardrefID)
            result = anvil.server.call("getFullnameInvoiceAmountAndBalance", jobcardrefID)
            
            if result:
                self.lbl_ClientName.text=result["Fullname"]
                self.lbl_TotalInvoiceAmount.text = result["TotalInvoiceAmount"]
                self.lbl_TotalAmountPaid.text=result["TotalAmountPaid"]
                self.lbl_TotalDiscount.text=result["TotalDiscount"]
                self.lbl_PaymentBalance.text=result["Balance"]

    
    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_SaveAndNew.enabled = False
    
        startDate = self.date_picker_start.date
        endDate = self.date_picker_end.date
        jobcardrefID = self.drop_down_1.selected_value
        fullname = self.lbl_ClientName.text
        invoiceTotal = self.lbl_TotalInvoiceAmount.text
        totalPaid = self.lbl_TotalAmountPaid.text
        totalDiscount = self.lbl_TotalDiscount.text
        balance = self.lbl_PaymentBalance.text
        rows = self.repeating_panel_1.items or []
    
        # --- Basic validation ---
        if startDate is None and endDate is None:
            alert("Sorry, please enter date period to proceed", title="Blank Field(s) Found")
            self.btn_SaveAndNew.enabled = True
            return
        elif startDate is None and endDate:
            alert("Sorry, please enter start date to proceed", title="Blank Field(s) Found")
            self.btn_SaveAndNew.enabled = True
            return
        elif startDate > endDate:
            alert("Sorry, start date cannot be greater than end date", title="Mismatch Dates")
            self.btn_SaveAndNew.enabled = True
            return
        elif jobcardrefID is None:
            alert("Sorry, please select the jobcard ref to proceed", title="Blank Field(s) Found")
            self.btn_SaveAndNew.enabled = True
            return
        elif not rows:
            alert("Sorry, ensure jobcard ref has parts or services associated with it",
                title="Missing Assigned Parts or Service", large=False)
            self.btn_SaveAndNew.enabled = True
            return
    
        # --- Validate Categories before saving ---
        for i, row in enumerate(rows, start=1):
            category = row.get('Category', None)
            if not category or str(category).strip() == "":
                item_name = row.get('Item', 'Unknown Item')
                alert(f"Missing category for item #{i}: {item_name}", title="Missing Category")
                self.btn_SaveAndNew.enabled = True
                return
    
        # --- Delete old monthly schedule to avoid duplicates ---
        anvil.server.call("deleteMonthlySchedule", jobcardrefID)

        # ---- Get Invoice Total Without Previous Balance, To Denote Amount Earned For That Period (E.G Month) ---
        for r in rows:
            if r.get('Category') == "Prev Bal":
                raw_string = r.get('Amount')
                raw = raw_string.replace(",", "")
                invoiceTotal = invoiceTotal - int(float(raw))
               
        # --- Insert new records ---
        for row in rows:
            invoiceDate = row.get('Date')
            item = row.get('Item')
            partNo = row.get('Part_No')
            quantity = row.get('QuantityIssued')
            amount = row.get('Amount')
            category = row.get('Category')
    
            anvil.server.call(
                "saveMonthlySchedule",
                invoiceDate, jobcardrefID, fullname,
                invoiceTotal, totalPaid, totalDiscount,
                balance, item, partNo,
                quantity, amount, category
            )
    
        alert("Categorized invoice details saved successfully", title="Success")
        self.btn_SaveAndNew.enabled = True
        self.clearForm()

    def clearForm(self, **event_args):
        self.date_picker_start.date=None
        self.date_picker_end.date = None
        self.drop_down_1.items=[]
        self.lbl_ClientName.text=""
        self.lbl_TotalInvoiceAmount.text=""
        self.lbl_TotalAmountPaid.text=""
        self.lbl_TotalDiscount.text=""
        self.lbl_PaymentBalance.text=""
        self.repeating_panel_1.items=[]

    def btn_ViewSchedule_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=ViewSchedule(), buttons=[], dismissible=False,large=True)
        
       