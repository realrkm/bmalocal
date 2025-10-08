from ._anvil_designer import InterimQuotationTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData
from ..TransitionInterimQuoteToInvoice import TransitionInterimQuoteToInvoice

class InterimQuotation(InterimQuotationTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors) #Set global server error handler
        self.drop_down_CheckInstaff.items = anvil.server.call('getInterimQuoteAndAmendedInvoiceStaff')
               

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)   
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)       

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_SearchCustomer_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        search_value = self.txtCustomerName.text.strip()

        if not search_value:
            alert("Please enter customer name to proceed.", title="Blank Field(s) Found", large=False)
            self.txtCustomerName.focus()
            return
            
        result = anvil.server.call('getClientNameAndPhoneNumber', search_value)

        if result:           
            #Clear drop down 
            self.drop_down_CustomerDetails.items = ""
            self.drop_down_CustomerDetails.items = result
        else:
            alert("No records found for the entered customer name.", title="Not Found")
            
    def drop_down_CustomerDetails_change(self, **event_args):
        """This method is called when an item is selected"""
        if self.drop_down_CustomerDetails.selected_value:
            existing_jobcard_details = anvil.server.call_s("getJobCardRowWithClientID", self.drop_down_CustomerDetails.selected_value)
            if existing_jobcard_details:
                self.txtMakeAndModel.text = existing_jobcard_details["MakeAndModel"]
                self.txtChassis.text = existing_jobcard_details["ChassisNo"]
                self.txtRegNo.text = existing_jobcard_details["RegNo"]
                self.txtEngineCode.text = existing_jobcard_details["EngineCode"]

                #Update textboxes in order to search for matching previous Interim Quotations
                self.txt_CustomerID.text = self.drop_down_CustomerDetails.selected_value
                self.txt_MakeAndModel.text = self.txtMakeAndModel.text
                self.txt_Chassis.text = self.txtChassis.text

                #Call function to search previous Interim Quotation
                self.getPreviousInterimQuoteDetails()
                
        elif self.drop_down_CustomerDetails.selected_value is None:
            self.txtMakeAndModel.text = ""
            self.txtChassis.text = ""
            self.txtRegNo.text =""
            self.txtEngineCode.text = ""


    def btn_Search_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        search_value = self.text_box_searchPartNo.text.strip()
        
        if not search_value:
            alert("Please enter part name or part no. to proceed.", title="Blank Field(s) Found", large=False)
            self.text_box_searchPartNo.focus()
            return
            
        result = anvil.server.call('getCarPartNameAndNumber', search_value)

        #Clear drop down 
        self.drop_down_selectPart.items = ""

        if result:
            self.drop_down_selectPart.items = result
        else:
            alert("No records found for the entered part detail.", title="Not Found")


    def drop_down_selectPart_change(self, **event_args):
        """This method is called when an item is selected"""
        self.lbl_ID.text = self.drop_down_selectPart.selected_value
        result2 =  anvil.server.call_s("getCarPartNumberWithID", self.lbl_ID.text)
        self.lbl_PartNumber.text = result2[0]["PartNo"]
        partname = anvil.server.call_s("getCarPartNamesWithId", self.drop_down_selectPart.selected_value)
        self.lbl_PartName.text = partname[0]["Name"]
        self.txtSellingPrice.text = ModGetData.getSellingPrice(self.lbl_ID.text)


    def btn_AddParts_click(self, **event_args):
        """This method is called when the button is clicked"""
        textAmount = str(self.txtSellingPrice.text).strip()
        
        if not self.drop_down_selectPart.selected_value:
            alert("Sorry, please select car part to proceed.", title="Blank Field(s) Found", large=False)
            self.drop_down_selectPart.focus()
            return
        if not self.txtQuantity.text:
            alert("Sorry, please enter quantity to proceed.", title="Blank Field(s) Found", large=False)
            self.txtQuantity.focus()
            return
        if textAmount == "":
            alert("Sorry, please enter selling price to proceed.", title="Blank Field(s) Found", large=False)
            self.txtSellingPrice.focus()
            return

        #Populate data grid with assigned parts
        new_part = {
            "Name": self.lbl_PartName.text,
            "Number": self.lbl_PartNumber.text,
            "Quantity": self.txtQuantity.text,
            "Amount": "TO BE CONFIRMED" if float(self.txtSellingPrice.text) == 0 else f"{float(self.txtSellingPrice.text):,.2f}"
        }

        # Append to the repeating panel's items
        current_items = self.repeating_panel_assigned_parts.items
        if not isinstance(current_items, list):
            current_items = []
        updated_items = current_items + [new_part]
        self.repeating_panel_assigned_parts.items = updated_items
        self.refresh()

        #Clear selected items
        self.text_box_searchPartNo.text = ""
        self.drop_down_selectPart.items = []
        self.txtQuantity.text =""
        self.txtSellingPrice.text =""

    def btn_AddServices_click(self, **event_args):
        """This method is called when the button is clicked"""
        textAmount = str(self.txtAmount.text).strip()

        if not self.txtServices.text:
            alert("Sorry, please enter service name to proceed.", title="Blank Field(s) Found", large=False)
            self.txtServices.focus()
            return

        if textAmount == "":
            alert("Sorry, please enter amount to proceed.", title="Blank Field(s) Found", large=False)
            self.txtAmount.focus()
            return

            
        #Populate data grid with assigned parts
        new_service = {
            "Name": self.txtServices.text,
            "Amount": "TO BE CONFIRMED" if float(self.txtAmount.text) == 0 else f"{float(self.txtAmount.text):,.2f}"
        }

        # Append to the repeating panel's items
        current_items2 = self.repeating_panel_assigned_parts.items
        if not isinstance(current_items2, list):
            current_items2 = []
        updated_items2 = current_items2 + [new_service]
        self.repeating_panel_assigned_parts.items = updated_items2
        self.refresh()

        #Clear selected items
        self.txtServices.text =""
        self.txtAmount.text =""

    def btn_SaveAndDownload_click(self, **event_args):
        self.btn_SaveAndDownload.enabled = False
        if not self.drop_down_CustomerDetails.selected_value:
            alert("Sorry, please search and select customer to proceed.", title="Blank Field(s) Found")
            self.txtCustomerName.focus()
            self.btn_SaveAndDownload.enabled = True
            return

        if not self.txtMakeAndModel.text:
            alert("Sorry, please enter make and model to proceed.", title="Blank Field(s) Found")
            self.txtMakeAndModel.focus()
            self.btn_SaveAndDownload.enabled = True
            return

        if not self.txtChassis.text:
            alert("Sorry, please enter chassis number to proceed.", title="Blank Field(s) Found")
            self.txtChassis.focus()
            self.btn_SaveAndDownload.enabled = True
            return

        if not self.date_picker_1.date:
            alert("Sorry, please enter date to proceed.", title="Blank Field(s) Found")
            self.date_picker_1.focus()
            self.btn_SaveAndDownload.enabled = True
            return

        if not self.drop_down_CheckInstaff.selected_value: # Required in tbl_jobcarddetails
            alert("Sorry, please select check-in staff to proceed.", title="Blank Field(s) Found", large=False)
            self.drop_down_CheckInstaff.focus()
            self.btn_SaveAndDownload.enabled = True
            return
            
        rows = self.repeating_panel_assigned_parts.items or []
        if not rows:
            anvil.alert("Sorry, please assign parts or service to proceed.", title="Missing Assigned Parts or Service")
            self.btn_SaveAndDownload.enabled = True
            return

        customerID = self.drop_down_CustomerDetails.selected_value
        makeandmodel=self.txtMakeAndModel.text
        chassis = self.txtChassis.text
        regno = self.txtRegNo.text
        enginecode = self.txtEngineCode.text
        receiveddate = self.date_picker_1.date
        duedate = self.date_picker_1.date
        mileage = self.txtMileage.text
        checkinstaff = self.drop_down_CheckInstaff.selected_value
        oldJobCardId = self.txt_OldJobCardID.text

        if (not regno or regno.strip() == "") and chassis and chassis.strip() != "":
            unique_identifier = chassis
        elif regno:
            unique_identifier = regno

        if mileage:
            jobcardref = f"{unique_identifier}-{mileage}-IQ"
        else:
            jobcardref = f"{unique_identifier}-{receiveddate.strftime('%Y-%m-%d')}-IQ"

        items = []
        for row in rows:
            item_name = row.get('Name', '')
            part_no = row.get('Number', "")
            quantity = float(row["Quantity"]) if row.get("Quantity") not in (None, "") else None
            
            if row["Amount"].upper() == "TO BE CONFIRMED":
                amount = 0
            else:
                amount = float(row["Amount"].replace(",", "")) if "," in row["Amount"] else float(row["Amount"])
                
            items.append({
                "name": item_name,
                "number": part_no,
                "quantity": quantity,
                "amount": amount
            })
        
        job_card_id = anvil.server.call_s('saveJobCardDetailsFromInterimQuotation', customerID, jobcardref, receiveddate, duedate, checkinstaff, regno, makeandmodel, chassis,  enginecode, mileage, oldJobCardId)
        anvil.server.call("saveInterimQuotationPartsAndServices",receiveddate, job_card_id, items)
        alert("Interim Quotation Saved Successfully.", title="Success", large=False)
        self.downloadQuotationPdf(job_card_id)
        
        # Clear form
        self.clear_form_fields()                     
        
    def downloadQuotationPdf(self, job_card_id):
        media_object = anvil.server.call('createQuotationInvoicePdf', job_card_id, "InterimQuotation")
        anvil.media.download(media_object)
        self.deleteFile(job_card_id, "InterimQuotation")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def clear_form_fields(self):
        """Helper function to clear all form fields after saving"""

        # Reset text fields
        self.txtCustomerName.text = ""
        self.txtMakeAndModel.text = ""
        self.txtChassis.text = ""
        self.txtRegNo.text = ""
        self.txtEngineCode.text = ""
        self.txtMileage.text = ""
        self.txtServices.text = ""
        self.txtAmount.text = ""
        self.text_box_searchPartNo.text = ""
        self.txtQuantity.text = ""
        self.txtSellingPrice.text = ""
    
        # Reset labels
        self.lbl_ID.text = ""
        self.lbl_PartNumber.text = ""
        self.lbl_PartName.text = ""
    
        # Reset dropdowns
        self.drop_down_CustomerDetails.items = []
        self.drop_down_CustomerDetails.selected_value = None
        self.drop_down_selectPart.items = []
        self.drop_down_selectPart.selected_value = None
        self.drop_down_CheckInstaff.items = anvil.server.call('getInterimQuoteAndAmendedInvoiceStaff')
        self.drop_down_CheckInstaff.selected_value = None
    
        # Reset date pickers
        self.date_picker_1.date = None
    
        # Clear repeating panel
        self.repeating_panel_assigned_parts.items = []

        #Clear hidden components
        self.txt_CustomerID.text = ""
        self.txt_MakeAndModel.text = ""
        self.txt_Chassis.text = ""
        self.date_Received.date = None
        self.txt_OldJobCardID.text = ""

        # Refresh form display
        self.refresh()
    
        # Restore focus
        self.txtCustomerName.focus()

        self.btn_SaveAndDownload.enabled = True

    def date_picker_1_change(self, **event_args):
        """This method is called when the selected date changes"""
        self.date_Received.date = self.date_picker_1.date
        self.getPreviousInterimQuoteDetails()

    def txtMakeAndModel_lost_focus(self, **event_args):
        """This method is called when the TextBox loses focus"""
        self.getPreviousInterimQuoteDetails()

    def txtChassis_lost_focus(self, **event_args):
        """This method is called when the TextBox loses focus"""
        self.getPreviousInterimQuoteDetails()

    def getPreviousInterimQuoteDetails(self):
        customerID = self.txt_CustomerID.text
        makeAndModel = self.txt_MakeAndModel.text
        chassis = self.txt_Chassis.text
        receivedDate= self.date_Received.date

        if customerID and makeAndModel and chassis and receivedDate:
            result = anvil.server.call("getPreviousInterimQuoteDetails", customerID, makeAndModel, chassis, receivedDate)
            if result:
                self.txt_OldJobCardID.text = result["job_details"]["JobCardID"]
                # Set parts to repeating panel
                self.repeating_panel_assigned_parts.items = result["parts"]
            
                alert("Previous details loaded successfully", title="Success")

    def btn_TransitionInterimQuoteToInvoice_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=TransitionInterimQuoteToInvoice(), buttons=[],dismissible=False, large=True)
        