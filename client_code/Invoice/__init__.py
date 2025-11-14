from ._anvil_designer import InvoiceTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData
from datetime import date


class Invoice(InvoiceTemplate):
    def __init__(self, valueID, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors) #Set global server error handler
        
        self.cmbJobCardRef.items =  ModGetData.getJobCardRef(valueID)
        
        # ✅ Select the first item if available
        if self.cmbJobCardRef.items:
            self.cmbJobCardRef.selected_value = self.cmbJobCardRef.items[0][1]
            # ✅ Manually call the change handler
            self.cmbJobCardRef_change()

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

    def cmbJobCardRef_change(self, **event_args):
        """This method is called when an item is selected"""
        self.txtClientInstructions.text = ModGetData.getJobCardInstructions(self.cmbJobCardRef.selected_value['ID'])
        self.txtTechNotes.text= ModGetData.getJobCardTechNotes(self.cmbJobCardRef.selected_value['ID'])
        self.txtDefectsList.text = ModGetData.getJobCardDefects(self.cmbJobCardRef.selected_value['ID'])
        self.txtRequestedParts.text = ModGetData.getRequestedParts(self.cmbJobCardRef.selected_value['ID'])
        self.repeating_panel_assigned_parts.items = ModGetData.getQuotationConfirmationFeedback(self.cmbJobCardRef.selected_value['ID'])

    def cmbCarParts_show(self, **event_args):
        """This method is called when the DropDown is shown on the screen"""
        self.cmbCarParts.items = ModGetData.getCarPartNames()
        self.refresh()

    def cmbCarParts_change(self, **event_args):
        """This method is called when an item is selected"""
        selected = self.cmbCarParts.selected_value
        if not selected:
            self.cmbPartNumber.selected_value = None
            self.cmbPartNumber.items= ""
            self.txtQuantity.text = ""
            self.txtSellingPrice.text = ""
        else:
            self.cmbPartNumber.selected_value = None
            self.cmbPartNumber.items = ModGetData.getCarPartNumber(selected['Name'])
            self.txtQuantity.text = ""
            self.txtSellingPrice.text = ""
            self.refresh()

    def cmbPartNumber_change(self, **event_args):
        """This method is called when an item is selected"""
        self.txtSellingPrice.text = ModGetData.getSellingPrice(self.cmbPartNumber.selected_value['ID'])
        
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
        textSellingPrice = str(self.txtSellingPrice.text).strip()
        
        if not self.drop_down_selectPart.selected_value:
            alert("Sorry, please select car part to proceed.", title="Blank Field(s) Found", large=False)
            self.drop_down_selectPart.focus()
            return
        if not self.txtQuantity.text:
            alert("Sorry, please enter quantity to proceed.", title="Blank Field(s) Found", large=False)
            self.txtQuantity.focus()
            return
        if textSellingPrice == "":
            alert("Sorry, please enter the selling price to proceed.", title="Blank Field(s) Found", large=False)
            self.txtSellingPrice.focus()
            return

        #Populate data grid with assigned parts
        new_part = {
            "Name": self.lbl_PartName.text,
            "Number": self.lbl_PartNumber.text,
            "Quantity": self.txtQuantity.text,
            "Amount": f"{float(self.txtSellingPrice.text):,.2f}",
            "CarPartID": self.lbl_ID.text
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
            "Amount": f"{float(self.txtAmount.text):,.2f}"
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

    def btn_Save_click(self, **event_args):
        self.btn_Save.enabled = False #Prevent multiple button clicks
        if not self.cmbJobCardRef.selected_value:
            alert("Sorry, please select job card ref to proceed.", title="Blank Field(s) Found")
            self.cmbJobCardRef.focus()
            self.btn_Save.enabled = True
            return

        if not self.cmbWorkflow.selected_value:
            alert("Sorry, please select the next workflow status to proceed.", title="Blank Field(s) Found")
            self.cmbWorkflow.focus()
            self.btn_Save.enabled = True
            return

        customerData = self.repeating_panel_assigned_parts.items or []
        if not customerData:
            anvil.alert("Sorry, please assign parts or service to proceed.", title="Missing Assigned Parts or Service")
            self.btn_Save.enabled = True
            return

        assignedDate = date.today()
        jobCardID = self.cmbJobCardRef.selected_value['ID']
        status = self.cmbWorkflow.selected_value

        items = []
        for row in customerData:
            item_name = row.get('Name')
            number = row.get('Number', "")
            quantity = None if row.get('Quantity') is None else float(row['Quantity'])
            amount = float(row["Amount"].replace(",", "")) if "," in row["Amount"] else float(row["Amount"])
            CarPartID_result = None # Initialize to None
            if number:
                # The server call might return a list [123] or None
                CarPartID_result = anvil.server.call("getCarPartIDWithNumber", number)
            # Check the result before trying to get an index
            final_id = CarPartID_result[0] if CarPartID_result else None
        
            items.append({
                "name": item_name,
                "number": number,
                "quantity": quantity,
                "amount": amount,
                "CarPartID": final_id # Use the variable that safely handles the None case
            })
        
        anvil.server.call('saveInvoice', assignedDate, jobCardID,  items)
        anvil.server.call_s('updateJobCardStatus', jobCardID, status)

        alert("Invoice saved successfully and download is initiated.", title="Success")
        self.downloadInvoicePdf(jobCardID)

        # Close Form
        self.btn_Close_click()
        self.refresh()

    def downloadInvoicePdf(self, jobCardID):
        media_object = anvil.server.call('createQuotationInvoicePdf', jobCardID, "Invoice")
        anvil.media.download(media_object)
        self.deleteFile(jobCardID, "Invoice")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)
        get_open_form().btn_Workflow_click()
  



    
