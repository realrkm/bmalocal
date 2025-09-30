from ._anvil_designer import OrderTrackingTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..UpdateOrderTracking import UpdateOrderTracking
from ..ViewImportOrderReport import ViewImportOrderReport


class OrderTracking(OrderTrackingTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        set_default_error_handling(self.handle_server_errors) #Set global server error handler

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
        
    def btn_SearchClient_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_term = self.txt_ClientDetails.text.strip()
        
        # 1. No filters selected
        if not search_term:
            alert("Sorry, please enter client details to proceed.", title="Blank Field(s) Found", large=False)
            return
        else:
            clientdetails = anvil.server.call('getClientNameAndPhoneNumber', search_term)
        
        if clientdetails:
            self.drop_down_selectrole.items = clientdetails
        else:
            alert("No records found for the entered keyword and or part name.", title="Not Found", large=False)

    def btn_SearchParts_click(self, **event_args):
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
        

    def btn_AddOrder_click(self, **event_args):
        """This method is called when the button is clicked"""
        if not self.drop_down_selectPart.selected_value:
            alert("Sorry, please select car part to proceed.", title="Blank Field(s) Found", large=False)
            self.drop_down_selectPart.focus()
            return
        if not self.txt_Quantity.text:
            alert("Sorry, please enter quantity to proceed.", title="Blank Field(s) Found", large=False)
            self.txt_Quantity.focus()
            return
        

        #Populate data grid with assigned parts
        new_part = {
            "Name": self.lbl_PartName.text,
            "Part_No": self.lbl_PartNumber.text,
            "Quantity": self.txt_Quantity.text,
            "Status": "Pending"
        }

        # Append to the repeating panel's items
        current_items = self.repeating_panel_1.items
        if not isinstance(current_items, list):
            current_items = []
        updated_items = current_items + [new_part]
        self.repeating_panel_1.items = updated_items
        self.refresh()

        #Clear selected items
        self.text_box_searchPartNo.text = ""
        self.drop_down_selectPart.items = []
        self.txt_Quantity.text =""
        

    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_SaveAndNew.enabled = False #Prevent multiple clicks

        if not self.drop_down_selectrole.selected_value:
            alert("Sorry, please select client to proceed.", title="Blank Field(s) Found", large=False)
            self.txt_ClientDetails.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not self.date_picker_1.date:
            alert("Sorry, please select date to proceed.", title="Blank Field(s) Found", large=False)
            self.date_picker_1.focus()
            self.btn_SaveAndNew.enabled = True
            return

        rows = self.repeating_panel_1.items or []

        if not rows:
            anvil.alert("Sorry, please assign parts to proceed.", title="Missing Assigned Parts", large=False)
            self.btn_SaveAndNew.enabled = True
            return


        orderDate= self.date_picker_1.date
        clientID=self.drop_down_selectrole.selected_value
        

        for row in rows:
            name= row['Name']
            number = row.get('Part_No', "")
            quantity = None if row.get('Quantity') is None else float(row['Quantity'])
            status = row["Status"]
            anvil.server.call('saveImportOrderTracking', orderDate, clientID, name, number, quantity, status)

        alert("Import order saved successfully.", title="Success")
        self.clearForm()
        self.refresh()
        self.btn_SaveAndNew.enabled = True


    def clearForm(self, **event_args):
        self.txt_ClientDetails.text = ""
        self.drop_down_selectrole.items=[]
        self.drop_down_selectrole.selected_value = None
        self.date_picker_1.date=None
        self.text_box_searchPartNo.text =""
        self.drop_down_selectPart.items=[]
        self.drop_down_selectPart.selected_value = None
        self.lbl_ID.text=""
        self.lbl_PartName.text=""
        self.lbl_PartNumber.text=""
        self.txt_Quantity.text=""
        self.repeating_panel_1.items=[]

    def btn_UpdateOrderTracking_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=UpdateOrderTracking(), dismissible=False, large=True, buttons=[])

    def btn_OrderReport_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=ViewImportOrderReport(), dismissible=False, large=True, buttons=[])
        
        