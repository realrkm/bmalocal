from ._anvil_designer import RepairPrioritiesTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import ModGetData
from datetime import date
import anvil.js

class RepairPriorities(RepairPrioritiesTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def btnSearch_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_text = self.txt_SearchRegNo.text.strip()
        
        if not search_text:
            alert("Please enter Reg No. to proceed.", title="Blank Field(s) Found", large=False)
            self.txt_SearchRegNo.focus()
            return

        result = anvil.server.call('getCarRegNo', search_text = self.txt_SearchRegNo.text)
        
        if result:
            self.drop_down_select.items = ""
            self.drop_down_select.items = result
        else:
            alert("No records found for the entered Reg No.", title="Not Found")

    def drop_down_select_change(self, **event_args):
        """This method is called when an item is selected"""
        self.repeating_panel_assigned_parts.items = anvil.server.call_s('getPriorityList', regNo=self.drop_down_select.selected_value)
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
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
            self.lbl_ID.text = result[0][1]
            result2 =  anvil.server.call_s("getCarPartNumberWithID", self.lbl_ID.text)
            self.lbl_PartNumber.text = result2[0]["PartNo"]
        else:
            alert("No records found for the entered part detail.", title="Not Found")

    def drop_down_selectPart_change(self, **event_args):
        """This method is called when an item is selected"""
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

        if not self.drop_down_selectPriority.selected_value:
            alert("Sorry, please select priority to proceed.", title="Blank Field(s) Found", large=False)
            self.drop_down_selectPriority.focus()
            return
            
        #Populate data grid with assigned parts
        new_part = {
            "Name": self.lbl_PartName.text,
            "Number": self.lbl_PartNumber.text,
            "Quantity": self.txtQuantity.text,
            "Amount": f"{float(self.txtSellingPrice.text):,.2f}",
            "Priority":self.drop_down_selectPriority.selected_value
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
        self.drop_down_selectPriority.selected_value=None

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

        if not self.drop_down_selectPriorityService.selected_value:
            alert("Sorry, please select priority to proceed.", title="Blank Field(s) Found", large=False)
            self.drop_down_selectPriorityService.focus()
            return
            
        #Populate data grid with assigned parts
        new_service = {
            "Name": self.txtServices.text,
            "Amount": f"{float(self.txtAmount.text):,.2f}",
            "Priority": self.drop_down_selectPriorityService.selected_value
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
        self.drop_down_selectPriorityService.selected_value=None

    def btn_Save_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Save.enabled = False #Prevent multiple clicks
        
        if not self.drop_down_select.selected_value:
            alert("Sorry, please select Reg No to proceed.", title="Blank Field(s) Found", large=False)
            self.drop_down_select.focus()
            self.btn_Save.enabled = True
            return
        
        rows = self.repeating_panel_assigned_parts.items or []
        
        if not rows:
            anvil.alert("Sorry, please assign parts or service to proceed.", title="Missing Assigned Parts or Service", large=False)
            self.btn_Save.enabled = True
            return
         
        #Delete current priority list for the selected reg no
        anvil.server.call_s('deleteCurrentPriority', self.drop_down_select.selected_value)
        
        assignedDate= date.today()
        regNo=self.drop_down_select.selected_value
        
        for row in rows:
            name= row['Name']
            number = row.get('Number', "")
            quantity = None if row.get('Quantity') is None else float(row['Quantity'])
            amount = float(row["Amount"].replace(",", "")) if "," in row["Amount"] else float(row["Amount"])
            priority = row["Priority"]
            anvil.server.call('savePriority', assignedDate, regNo, name, number, quantity, amount, priority)
            
        alert("Priority saved successfully and download is initiated", title="Success")
        self.downloadPriorityPdf(regNo)
        # Clear form
        self.clear_form_fields()
        
    def downloadPriorityPdf(self, regNo):
        media_object = anvil.server.call('downloadRevisionPdfForm', regNo, "Priority")
        anvil.media.download(media_object)
        self.deleteFile(regNo, "Priority")
    
    def deleteFile(self, regNo, docType):
        anvil.server.call("deleteRevisionFile", regNo, docType)
    
    def btn_DeleteRow_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.remove_from_parent()
    
    def btn_Download_click(self, **event_args):
        """This method is called when the button is clicked"""
    
        if not self.drop_down_select.selected_value:
            alert("Sorry, please select Reg No to proceed.", title="Blank Field(s) Found", large=False)
            self.drop_down_select.focus()
            return
        
        elif self.drop_down_select.selected_value:
            existingData = anvil.server.call_s("getPriorityList", self.drop_down_select.selected_value)
            if existingData:
                self.downloadPriorityPdf(self.drop_down_select.selected_value)
            else:
                alert("Sorry, there's no priority list found for the Reg No", title="Missing Priority List", large=False)
                self.drop_down_select.focus()
                return

    def clear_form_fields(self):
        """Reset all form fields and clear the repeating panel."""
        self.txt_SearchRegNo.text = ""
        self.drop_down_select.items = []
        self.drop_down_select.selected_value = None
        self.text_box_searchPartNo.text = ""
        self.drop_down_selectPart.items = []
        self.drop_down_selectPart.selected_value = None
        self.lbl_ID.text = ""
        self.lbl_PartNumber.text = ""
        self.lbl_PartName.text = ""
        self.txtQuantity.text = ""
        self.txtSellingPrice.text = ""
        self.drop_down_selectPriority.selected_value = None
        self.txtServices.text = ""
        self.txtAmount.text = ""
        self.drop_down_selectPriorityService.selected_value = None
        self.repeating_panel_assigned_parts.items = []

        self.btn_Save.enabled = True