from ._anvil_designer import InterimQuotationTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData
from .. import ModCache


class InterimQuotation(InterimQuotationTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        self._customer_jc_cache = {}
        self._part_details_cache = {}
        self._prewarmed_transition_modal = None
        self.set_event_handler("show", self._on_form_show)

        cached_staff = ModCache.get_cached("interim_staff")
        if cached_staff is not None:
            self.drop_down_CheckInstaff.items = cached_staff
        else:
            try:
                anvil.js.window.setTimeout(self._hydrate_staff_dropdown, 0)
            except Exception:
                self._hydrate_staff_dropdown()

    def _hydrate_staff_dropdown(self):
        try:
            with anvil.server.no_loading_indicator:
                self.drop_down_CheckInstaff.items = ModGetData.getInterimStaffCached()
        except Exception:
            pass

    def _on_form_show(self, **event_args):
        if self._prewarmed_transition_modal is None:
            try:
                anvil.js.window.setTimeout(self._prewarm_transition_modal, 30)
            except Exception:
                pass

    def _prewarm_transition_modal(self):
        if self._prewarmed_transition_modal is not None:
            return
        try:
            from ..TransitionInterimQuoteToInvoice import TransitionInterimQuoteToInvoice
            self._prewarmed_transition_modal = TransitionInterimQuoteToInvoice()
        except Exception:
            self._prewarmed_transition_modal = None

    def _speculative_warm_customer(self, client_id):
        if not client_id or client_id in self._customer_jc_cache:
            return
        try:
            with anvil.server.no_loading_indicator:
                self._customer_jc_cache[client_id] = anvil.server.call_s("getJobCardRowWithClientID", client_id)
        except Exception:
            pass

    def _speculative_warm_part(self, part_id):
        if not part_id or part_id in self._part_details_cache:
            return
        try:
            with anvil.server.no_loading_indicator:
                self._part_details_cache[part_id] = anvil.server.call_s("get_part_edit_details", part_id)
        except Exception:
            pass

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_SearchCustomer_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        search_value = self.txtCustomerName.text.strip()

        if not search_value:
            Notification("Please enter customer name to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtCustomerName.focus()
            return

        result = anvil.server.call('getClientNameAndPhoneNumber', search_value)

        if result:
            self.drop_down_CustomerDetails.items = ""
            self.drop_down_CustomerDetails.items = result
            first_client_id = result[0][1]
            try:
                anvil.js.window.setTimeout(lambda: self._speculative_warm_customer(first_client_id), 0)
            except Exception:
                pass
        else:
            Notification("No records found for the entered customer name.", title="Not Found", style="danger", timeout=3).show()

    def drop_down_CustomerDetails_change(self, **event_args):
        """This method is called when an item is selected"""
        selected_client = self.drop_down_CustomerDetails.selected_value
        if selected_client:
            if selected_client in self._customer_jc_cache:
                existing_jobcard_details = self._customer_jc_cache[selected_client]
            else:
                existing_jobcard_details = anvil.server.call_s("getJobCardRowWithClientID", selected_client)
                self._customer_jc_cache[selected_client] = existing_jobcard_details
            if existing_jobcard_details:
                self.txtMakeAndModel.text = existing_jobcard_details["MakeAndModel"]
                self.txtChassis.text = existing_jobcard_details["ChassisNo"]
                self.txtRegNo.text = existing_jobcard_details["RegNo"]
                self.txtEngineCode.text = existing_jobcard_details["EngineCode"]

                # Update textboxes in order to search for matching previous Interim Quotations
                self.txt_CustomerID.text = selected_client
                self.txt_MakeAndModel.text = self.txtMakeAndModel.text
                self.txt_Chassis.text = self.txtChassis.text

                # Call function to search previous Interim Quotation
                self.getPreviousInterimQuoteDetails()

        elif selected_client is None:
            self.txtMakeAndModel.text = ""
            self.txtChassis.text = ""
            self.txtRegNo.text = ""
            self.txtEngineCode.text = ""


    def btn_Search_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        search_value = self.text_box_searchPartNo.text.strip()

        if not search_value:
            Notification("Please enter part name or part no. to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.text_box_searchPartNo.focus()
            return

        result = anvil.server.call('getCarPartNameAndNumber', search_value)

        self.drop_down_selectPart.items = ""

        if result:
            self.drop_down_selectPart.items = result
            first_part_id = result[0][1]
            try:
                anvil.js.window.setTimeout(lambda: self._speculative_warm_part(first_part_id), 0)
            except Exception:
                pass
        else:
            Notification("No records found for the entered part detail.", title="Not Found", style="danger", timeout=3).show()


    def drop_down_selectPart_change(self, **event_args):
        """This method is called when an item is selected"""
        part_id = self.drop_down_selectPart.selected_value
        self.lbl_ID.text = part_id
        if not part_id:
            return
        details = self._part_details_cache.get(part_id)
        if details is None:
            details = anvil.server.call_s("get_part_edit_details", part_id)
            if details:
                self._part_details_cache[part_id] = details
        if not details:
            return
        self.lbl_PartNumber.text = details["part_no"]
        self.lbl_PartName.text = details["part_name"]
        selling = details.get("selling_details")
        if selling is None or selling.get("Amount") is None:
            ModGetData.trackMissingPrice(part_id)
            Notification("Sorry, please enter selling price to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtSellingPrice.text = None
        else:
            self.txtSellingPrice.text = selling["Amount"]


    def btn_AddParts_click(self, **event_args):
        """This method is called when the button is clicked"""
        textAmount = str(self.txtSellingPrice.text).strip()
        
        if not self.drop_down_selectPart.selected_value:
            Notification("Sorry, please select car part to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.drop_down_selectPart.focus()
            return
        if not self.txtQuantity.text:
            Notification("Sorry, please enter quantity to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtQuantity.focus()
            return
        if textAmount == "":
            Notification("Sorry, please enter selling price to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtSellingPrice.focus()
            return

        # Get current items first
        current_items = self.repeating_panel_assigned_parts.items
        if not isinstance(current_items, list):
            current_items = []

        # Check for duplicate using Name and Number (case-insensitive)
        selected_name = self.lbl_PartName.text.strip().lower()
        selected_number = self.lbl_PartNumber.text.strip().lower()
        already_exists = any(
            item["Name"].strip().lower() == selected_name and
            item["Number"].strip().lower() == selected_number
            for item in current_items
        )

        if already_exists:
            alert(
                f"'{self.lbl_PartName.text}' has already been added.",
                title="Duplicate Part",
                large=False
            )
            return
            
        #Populate data grid with assigned parts
        new_part = {
            "Name": self.lbl_PartName.text,
            "Number": self.lbl_PartNumber.text,
            "Quantity": self.txtQuantity.text,
            "Amount": "TO BE CONFIRMED" if float(self.txtSellingPrice.text) == 0 else f"{float(self.txtSellingPrice.text):,.2f}"
        }

        # If this part had no price in the DB, record what the user typed
        ModGetData.recordManualPrice(self.lbl_ID.text, self.txtSellingPrice.text)

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
            Notification("Sorry, please enter service name to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtServices.focus()
            return

        if textAmount == "":
            Notification("Sorry, please enter amount to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtAmount.focus()
            return

        # Get current items first
        current_items2 = self.repeating_panel_assigned_parts.items
        if not isinstance(current_items2, list):
            current_items2 = []

        # Check for duplicate using service Name (case-insensitive)
        entered_name = self.txtServices.text.strip().lower()
        already_exists = any(item["Name"].strip().lower() == entered_name for item in current_items2)

        if already_exists:
            alert(
                f"'{self.txtServices.text.strip()}' has already been added.",
                title="Duplicate Service",
                large=False
            )
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

    def insertMissingSellingPrices(self):
        """
        Delegates to ModGetData to update any parts that had no selling price
        in the DB but received a manual price from the user.
        """
        ModGetData.insertMissingSellingPrice()

    def btn_SaveAndDownload_click(self, **event_args):
        self.btn_SaveAndDownload.enabled = False
        if not self.drop_down_CustomerDetails.selected_value:
            Notification("Sorry, please search and select customer to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtCustomerName.focus()
            self.btn_SaveAndDownload.enabled = True
            return

        if not self.txtMakeAndModel.text:
            Notification("Sorry, please enter make and model to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtMakeAndModel.focus()
            self.btn_SaveAndDownload.enabled = True
            return

        if not self.txtChassis.text:
            Notification("Sorry, please enter chassis number to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtChassis.focus()
            self.btn_SaveAndDownload.enabled = True
            return

        if not self.date_picker_1.date:
            Notification("Sorry, please enter date to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.date_picker_1.focus()
            self.btn_SaveAndDownload.enabled = True
            return

        if not self.drop_down_CheckInstaff.selected_value: # Required in tbl_jobcarddetails
            Notification("Sorry, please select check-in staff to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.drop_down_CheckInstaff.focus()
            self.btn_SaveAndDownload.enabled = True
            return
            
        rows = self.repeating_panel_assigned_parts.items or []
        if not rows:
            Notification("Sorry, please assign parts or service to proceed.", title="Missing Assigned Parts or Service", style="warning", timeout=3).show()
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
        Notification("Interim Quotation Saved Successfully.", title="Success", style="success", timeout=3).show()
        self.insertMissingSellingPrices()
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
        self.drop_down_CheckInstaff.items = ModGetData.getInterimStaffCached()
        self.drop_down_CheckInstaff.selected_value = None
        self._customer_jc_cache.clear()
    
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
            
                Notification("Previous details loaded successfully", title="Success", style="success", timeout=3).show()

    def btn_TransitionInterimQuoteToInvoice_click(self, **event_args):
        """Open pre-warmed TransitionInterimQuoteToInvoice modal immediately."""
        modal = self._prewarmed_transition_modal
        self._prewarmed_transition_modal = None
        if modal is None:
            from ..TransitionInterimQuoteToInvoice import TransitionInterimQuoteToInvoice
            modal = TransitionInterimQuoteToInvoice()
        alert(content=modal, buttons=[], dismissible=False, large=True)
        try:
            anvil.js.window.setTimeout(self._prewarm_transition_modal, 15)
        except Exception:
            pass
        