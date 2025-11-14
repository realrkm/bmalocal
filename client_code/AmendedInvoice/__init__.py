from ._anvil_designer import AmendedInvoiceTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


class AmendedInvoice(AmendedInvoiceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
            
        set_default_error_handling(
            self.handle_server_errors
        )  # Set global server error handler
       

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert(
                "Connection to server lost. Please check your internet or try again later.",
                title="Disconnected",
                large=False,
            )
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert(
                "Please connect to the internet to proceed.",
                title="No Internet",
                large=False,
            )
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_SearchCustomer_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        search_text = self.txtJobCardRef.text.strip()

        if not search_text:
            alert("Please enter job card ref to search.", title="Missing Job Card Ref")
            self.txtJobCardRef.focus()
            return

        result = anvil.server.call("getJobCardRefInvoiceDetails", search_text)
        
        if result:
            # Clear drop down
            self.drop_down_JobCardRefDetails.items = ""
            self.drop_down_JobCardRefDetails.items = result
        else:
             alert("No records found for the entered job card ref.", title="Not Found")

    def drop_down_JobCardRefDetails_change(self, **event_args):
        """This method is called when an item is selected"""
        if self.drop_down_JobCardRefDetails.selected_value:
            existing_jobcard_details = anvil.server.call_s(
                "get_invoice_details_by_job_id",
                self.drop_down_JobCardRefDetails.selected_value,
            )            
            if existing_jobcard_details:
                self.label_MakeAndModel.text = existing_jobcard_details[0]["MakeAndModel"]
                self.label_Chassis.text = existing_jobcard_details[0]["ChassisNo"]
                self.label_RegNo.text = existing_jobcard_details[0]["RegNo"]
                self.label_EngineCode.text = existing_jobcard_details[0]["EngineCode"]
                self.date_picker_1.date = existing_jobcard_details[0]["Date"]
                self.label_Mileage.text = existing_jobcard_details[0]['Mileage']
                
                items_append = []
                for x in existing_jobcard_details:
                    items_append.append({
                        "Item": x["Item"],
                        "PartNo": x["PartNo"],
                        "QuantityIssued":x["QuantityIssued"],
                        "Amount":f"{float(x['Amount']):,.2f}"
                    })
                self.repeating_panel_assigned_parts.items = items_append
                
        elif self.drop_down_JobCardRefDetails.selected_value is None:
            self.label_MakeAndModel.text = ""
            self.label_Chassis.text = ""
            self.label_RegNo.text = ""
            self.label_EngineCode.text = ""
            self.date_picker_1.date = ""
            self.label_Mileage.text = ""
            

    def btn_Search_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        search_value = self.text_box_searchPartNo.text.strip()

        if not search_value:
            alert("Please enter part name or part number to search.", title="Missing Part Details")
            self.text_box_searchPartNo.focus()
            return
            
        result = anvil.server.call("getCarPartNameAndNumber", search_value)
        
        # Clear drop down
        self.drop_down_selectPart.items = ""

        if result:
            self.drop_down_selectPart.items = result
        else:
            alert("No records found for the entered part detail.", title="Not Found")

    def drop_down_selectPart_change(self, **event_args):
        """This method is called when an item is selected"""
        self.lbl_ID.text = self.drop_down_selectPart.selected_value
        result2 = anvil.server.call_s("getCarPartNumberWithID", self.lbl_ID.text)
        self.lbl_PartNumber.text = result2[0]["PartNo"]
        partname = anvil.server.call_s(
            "getCarPartNamesWithId", self.drop_down_selectPart.selected_value
        )
        self.lbl_PartName.text = partname[0]["Name"]
        self.txtSellingPrice.text = ModGetData.getSellingPrice(self.lbl_ID.text)

    def btn_AddParts_click(self, **event_args):
        """This method is called when the button is clicked"""
        if not self.drop_down_selectPart.selected_value:
            alert(
                "Sorry, please select car part to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.drop_down_selectPart.focus()
            return
        if not self.txtQuantity.text:
            alert(
                "Sorry, please enter quantity to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtQuantity.focus()
            return
        if self.txtSellingPrice.text =="":
            alert(
                "Sorry, please enter selling price to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtSellingPrice.focus()
            return

        # Populate data grid with assigned parts
        new_part = {
            "Item": self.lbl_PartName.text,
            "PartNo": self.lbl_PartNumber.text,
            "QuantityIssued": self.txtQuantity.text,
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

        # Clear selected items
        self.text_box_searchPartNo.text = ""
        self.drop_down_selectPart.items = []
        self.txtQuantity.text = ""
        self.txtSellingPrice.text = ""

    def btn_AddServices_click(self, **event_args):
        """This method is called when the button is clicked"""
        if not self.txtServices.text:
            alert(
                "Sorry, please enter service name to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtServices.focus()
            return

        if self.txtAmount.text =="":
            alert(
                "Sorry, please enter amount to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtAmount.focus()
            return

        # Populate data grid with services
        new_service = {
            "Item": self.txtServices.text,
            "Amount": f"{float(self.txtAmount.text):,.2f}",
        }

        # Append to the repeating panel's items
        current_items2 = self.repeating_panel_assigned_parts.items
        if not isinstance(current_items2, list):
            current_items2 = []
        updated_items2 = current_items2 + [new_service]
        self.repeating_panel_assigned_parts.items = updated_items2
        self.refresh()

        # Clear selected items
        self.txtServices.text = ""
        self.txtAmount.text = ""

    

    def btn_AddVAT_click(self, **event_args):
        """This method is called when the button is clicked"""
    
        # Ensure VAT field is filled
        if not self.txtVAT.text:
            alert(
                "Sorry, please enter VAT amount (e.g 16) to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtVAT.focus()
            return
    
        # Convert VAT text to number safely
        try:
            vat_percent = float(str(self.txtVAT.text).replace("%", "").strip())
        except ValueError:
            alert("Invalid VAT value. Please enter a number like 16 or 16%.")
            self.txtVAT.focus()
            return
    
        # Get current parts or services list
        current_items4 = self.repeating_panel_assigned_parts.items
        if not isinstance(current_items4, list) or len(current_items4) == 0:
            alert(
                "Sorry, please enter parts or services first, in order to calculate VAT.",
                title="Missing Parts Or Services",
            )
            return
    
        # Compute total before VAT (remove commas)
        total_amount = 0.0

        for row in current_items4:
            # Clean up Amount (remove commas)
            amount_str = str(row.get("Amount", "")).replace(",", "").strip()
            qty = row.get("QuantityIssued")
            if not amount_str:
                continue  # skip if Amount is missing or empty
        
            try:
                amount = float(amount_str)
                if row.get("Item") != "Previous Balance" and isinstance(qty, int):
                    total_amount += amount * float(qty)
                elif row.get("Item") != "Previous Balance" and isinstance(qty, str):
                    total_amount += amount
            except ValueError:
                # Skip invalid numeric values gracefully
                continue
    
        # Calculate VAT
        vat_amount = (vat_percent / 100) * total_amount
    
        # Add VAT as a new row
        new_VAT = {
            "Item": f"{int(vat_percent)}% VAT",
            "Amount": f"{vat_amount:,.2f}",  # formatted nicely
        }
    
        # Update repeating panel
        updated_items4 = current_items4 + [new_VAT]
        self.repeating_panel_assigned_parts.items = updated_items4
        self.refresh()
    
        # Clear VAT input
        self.txtVAT.text = ""

    def btn_AddPreviousBalance_click(self, **event_args):
        """This method is called when the button is clicked"""

        if not self.txtPreviousAmount.text:
            alert(
                "Sorry, please enter previous balance amount to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtPreviousAmount.focus()
            return

            # Populate data grid with previous balance
        new_service = {
            "Item": "Previous Balance",
            "Amount": f"{float(self.txtPreviousAmount.text):,.2f}",
        }

        # Append to the repeating panel's items
        current_items3 = self.repeating_panel_assigned_parts.items
        if not isinstance(current_items3, list):
            current_items3 = []
        updated_items3 = current_items3 + [new_service]
        self.repeating_panel_assigned_parts.items = updated_items3
        self.refresh()

        # Clear selected items
        self.txtPreviousAmount.text = ""
        
    def btn_SaveAndDownload_click(self, **event_args):
        self.btn_SaveAndDownload.enabled = False
        
        if not self.drop_down_JobCardRefDetails.selected_value:
            alert(
                "Sorry, please search and select job card ref to proceed.",
                title="Blank Field(s) Found",
            )
            self.txtJobCardRef.focus()
            self.btn_SaveAndDownload.enabled = True
            return
        
        if not self.date_picker_1.date:
            alert("Sorry, please enter date to proceed.", title="Blank Field(s) Found")
            self.date_picker_1.focus()
            self.btn_SaveAndDownload.enabled = True
            return


        rows = self.repeating_panel_assigned_parts.items or []
        if not rows:
            anvil.alert(
                "Sorry, please assign parts or service to proceed.",
                title="Missing Assigned Parts or Service",
            )
            self.btn_SaveAndDownload.enabled = True
            return

        # ✅ Check if any item has "Previous Balance"
        has_previous_balance = any(
            item.get("Item", "").strip().lower() == "previous balance"
            for item in rows
        )

        if has_previous_balance:
        # Sort so that "Previous Balance" is last
            rows = sorted(
                rows, key=lambda x: x["Item"].strip().lower() == "previous balance"
            )
        
        items = []
        for row in rows:
            item_name = row.get("Item", "")
            part_no = row.get("PartNo", "")
            quantity = float(row["QuantityIssued"]) if row.get("QuantityIssued") not in (None, "") else None
            if not isinstance(row["Amount"], int): # Repeating panel loads amount as int values when job card ref is selected, hence skip int values
                amount = (
                    float(row["Amount"].replace(",", ""))
                    if "," in row["Amount"]
                    else float(row["Amount"])
                )
            else:
                amount = float(row["Amount"])

            CarPartID_result = None # Initialize to None
            if part_no:
                # The server call might return a list [123] or None
                CarPartID_result = anvil.server.call("getCarPartIDWithNumber", part_no)
            # Check the result before trying to get an index
            final_id = CarPartID_result[0] if CarPartID_result else None

            items.append({
                "name": item_name,
                "number": part_no,
                "quantity": quantity,
                "amount": amount,
                "CarPartID": final_id # Use the variable that safely handles the None case
            })

        invoicedate = self.date_picker_1.date
        job_card_id = self.drop_down_JobCardRefDetails.selected_value
        
        anvil.server.call(
            "updateInvoice", invoicedate, job_card_id, items
        )
        alert("Amended Invoice Saved Successfully.", title="Success", large=False)
        self.downloadInvoicePdf(job_card_id)

        # Clear form
        self.clear_form_fields()

    def downloadInvoicePdf(self, job_card_id):
        media_object = anvil.server.call(
            "createQuotationInvoicePdf", job_card_id, "Invoice"
        )
        anvil.media.download(media_object)
        self.deleteFile(job_card_id, "Invoice")

    def deleteFile(self, jobCardID, docType):
        anvil.server.call("deleteFile", jobCardID, docType)

    def clear_form_fields(self):
        """Helper function to clear all form fields after saving"""

        # Reset text boxes
        self.txtJobCardRef.text = ""
        self.text_box_searchPartNo.text = ""
        self.txtQuantity.text = ""
        self.txtSellingPrice.text = ""
        self.txtServices.text = ""
        self.txtAmount.text = ""
        self.txtPreviousAmount.text = ""
    
        # Reset labels
        self.label_MakeAndModel.text = ""
        self.label_Chassis.text = ""
        self.label_RegNo.text = ""
        self.label_EngineCode.text = ""
        self.label_Mileage.text = ""
        self.lbl_ID.text = ""
        self.lbl_PartNumber.text = ""
        self.lbl_PartName.text = ""
    
        # Reset dropdowns
        self.drop_down_JobCardRefDetails.items = []
        self.drop_down_JobCardRefDetails.selected_value = None
        self.drop_down_selectPart.items = []
        self.drop_down_selectPart.selected_value = None
    
        # Reset date picker
        self.date_picker_1.date = None
    
        # Clear repeating panel
        self.repeating_panel_assigned_parts.items = []
    
        # Refresh form
        self.refresh()
    
        # Restore focus for convenience
        self.txtJobCardRef.focus()

        self.btn_SaveAndDownload.enabled = True

    

  
