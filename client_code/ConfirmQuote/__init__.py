from ._anvil_designer import ConfirmQuoteTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.media
import anvil.js
from .. import ModGetData
from ..EditQuote import EditQuote
from datetime import date

class ConfirmQuote(ConfirmQuoteTemplate):
    def __init__(self, valueID, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.cmbJobCardRef.items =  ModGetData.getJobCardRef(valueID)
        # ✅ Select the first item if available
        if self.cmbJobCardRef.items:
            self.cmbJobCardRef.selected_value = self.cmbJobCardRef.items[0][1]
            # ✅ Manually call the change handler
            self.cmbJobCardRef_change()

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def cmbJobCardRef_change(self, **event_args):
        """This method is called when an item is selected"""
        self.txtClientInstructions.text = ModGetData.getJobCardInstructions(self.cmbJobCardRef.selected_value['ID'])
        self.txtTechNotes.text= ModGetData.getJobCardTechNotes(self.cmbJobCardRef.selected_value['ID'])
        self.txtDefectsList.text = ModGetData.getJobCardDefects(self.cmbJobCardRef.selected_value['ID'])
        self.txtRequestedParts.text = ModGetData.getRequestedParts(self.cmbJobCardRef.selected_value['ID'])
        self.txtQuoteConfirmationFeedback.focus()

        #If JobCardId exists in tbl_quotationpartsandservicesfeedback, then this is multiple confirmation taking place between client and internal user
        result = anvil.server.call("getQuotationConfirmationFeedback", self.cmbJobCardRef.selected_value['ID'])
        if result:
            self.repeating_panel_assigned_parts.items = result
        else:
            self.repeating_panel_assigned_parts.items = anvil.server.call("populate_confirmation_from_quote", self.cmbJobCardRef.selected_value['ID'])


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
        if not self.drop_down_selectPart.selected_value:
            alert("Sorry, please select car part to proceed.", title="Blank Field(s) Found", large=False)
            self.drop_down_selectPart.focus()
            return
        if not self.txtQuantity.text:
            alert("Sorry, please enter quantity to proceed.", title="Blank Field(s) Found", large=False)
            self.txtQuantity.focus()
            return
        if not self.txtSellingPrice.text:
            alert("Sorry, please enter selling price to proceed.", title="Blank Field(s) Found", large=False)
            self.txtSellingPrice.focus()
            return

        #Populate data grid with assigned parts
        new_part = {
            "Name": self.lbl_PartName.text,
            "Number": self.lbl_PartNumber.text,
            "Quantity": self.txtQuantity.text,
            "Amount": f"{float(self.txtSellingPrice.text):,.2f}"
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
        if not self.txtServices.text:
            alert("Sorry, please enter service name to proceed.", title="Blank Field(s) Found", large=False)
            self.txtServices.focus()
            return

        if not self.txtAmount.text:
            alert("Sorry, please enter amount to proceed.", title="Blank Field(s) Found", large=False)
            self.txtAmount.focus()
            return

        #Populate data grid with assigned parts
        new_service = {
            "Name": self.txtServices.text,
            "Amount": f"{self.txtAmount.text:,.2f}"
        }

        # Append to the repeating panel's items
        current_items2 = self.repeating_panel_assigned_parts.items or []
        updated_items2 = current_items2 + [new_service]
        self.repeating_panel_assigned_parts.items = updated_items2
        self.refresh()

        #Clear selected items
        self.txtServices.text =""
        self.txtAmount.text =""

    def btn_Save_click(self, **event_args):
        self.btn_Save.enabled = False #Prevent multiple clicks
        
        if not self.cmbJobCardRef.selected_value:
            alert("Sorry, please select job card ref to proceed.", title="Blank Field(s) Found")
            self.cmbJobCardRef.focus()
            self.btn_Save.enabled=True
            return
    
        if not self.txtQuoteConfirmationFeedback.text:
            alert("Sorry, please enter quote confirmation feedback to proceed.", title="Blank Field(s) Found")
            self.txtQuoteConfirmationFeedback.focus()
            self.btn_Save.enabled=True
            return

        if not self.cmbWorkflow.selected_value:
            alert("Sorry, please select the next workflow status to proceed.", title="Blank Field(s) Found")
            self.cmbWorkflow.focus()
            self.btn_Save.enabled=True
            return
    
        rows = self.repeating_panel_assigned_parts.items or []
        if not rows:
            anvil.alert("Sorry, please assign parts or service to proceed.", title="Missing Assigned Parts or Service")
            self.btn_Save.enabled=True
            return
    
        assignedDate = date.today()
        jobCardID = self.cmbJobCardRef.selected_value['ID']
        remarks = self.txtQuoteConfirmationFeedback.text
        status = self.cmbWorkflow.selected_value
    
        items = []
        for row in rows:
            item_name = row.get('Name', '')
            part_no = row.get('Number', "")
            quantity = row.get("Quantity") 
            
            amount_raw = row.get("Amount") or 0
            if ',' in str(amount_raw):
                cleaned_amount = str(amount_raw).replace(',', '')
                amount = float(cleaned_amount)
            else:
                amount = float(amount_raw)
                
            items.append({
                "name": item_name,
                "number": part_no,
                "quantity": quantity,
                "amount": amount
            })
    
        try:
            
            anvil.server.call_s('saveFullQuotationPartsAndServicesFeedback', assignedDate, jobCardID, remarks, items)
            anvil.server.call_s('updateJobCardStatus', jobCardID, status)
            
            alert("Quotation confirmation saved successfully", title="Success")
        except anvil.server.UplinkDisconnectedError:
            alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected")
        except anvil.server.SessionExpiredError:
            anvil.js.window.location.reload()
        except anvil.server.AppOfflineError:
            alert("Please connect to the internet to proceed.", title="No Internet")
        except Exception as e:
            alert(f"An error occurred: {str(e)}", title="Error")
    
        self.downloadQuotationPdf(jobCardID)

        # Close Form
        self.btn_Close_click()
        self.refresh()

    def downloadQuotationPdf(self, jobCardID):
        media_object = anvil.server.call('createQuotationInvoicePdf', jobCardID, "Confirm Quotation")
        anvil.media.download(media_object)
        self.deleteFile(jobCardID, "Confirm Quotation")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)
        
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)
        get_open_form().btn_Workflow_click()

