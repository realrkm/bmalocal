from ._anvil_designer import BrandComparisonTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import ModGetData
from datetime import date
import anvil.js


class BrandComparison(BrandComparisonTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        self._brand_cache = {}
        self._part_details_cache = {}

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def _speculative_warm_brand(self, reg_no):
        if not reg_no or reg_no in self._brand_cache:
            return
        try:
            with anvil.server.no_loading_indicator:
                self._brand_cache[reg_no] = anvil.server.call_s("getBrandComparisonList", regNo=reg_no)
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

    def btnSearch_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_value = self.txt_SearchRegNo.text.strip()

        if not search_value:
            Notification("Please enter RegNo to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txt_SearchRegNo.focus()
            return

        result = anvil.server.call("getCarRegNo", search_text=self.txt_SearchRegNo.text)

        if result:
            self.drop_down_select.items = ""
            self.drop_down_select.items = result
            first_reg = result[0][1] if isinstance(result[0], (list, tuple)) else result[0]
            try:
                anvil.js.window.setTimeout(lambda: self._speculative_warm_brand(first_reg), 0)
            except Exception:
                pass
        else:
            Notification("No records found for the entered Reg No.", title="Not Found", style="danger", timeout=3).show()

    def drop_down_select_change(self, **event_args):
        """This method is called when an item is selected"""
        reg_no = self.drop_down_select.selected_value
        if not reg_no:
            self.repeating_panel_assigned_parts.items = []
            return
        if reg_no in self._brand_cache:
            self.repeating_panel_assigned_parts.items = list(self._brand_cache[reg_no])
        else:
            items = anvil.server.call_s("getBrandComparisonList", regNo=reg_no)
            self._brand_cache[reg_no] = items
            self.repeating_panel_assigned_parts.items = items

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
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
        """Populate part name, number, and selling price in a single bundled lookup."""
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
            
        if textAmount == "":
            alert(
                "Sorry, please enter selling price to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtSellingPrice.focus()
            return
        if not self.txtGroupParts.text:
            alert(
                "Sorry, please enter group number to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtGroupParts.focus()
            return

        # Populate data grid with assigned parts
        new_part = {
            "Name": self.lbl_PartName.text,
            "Number": self.lbl_PartNumber.text,
            "Quantity": self.txtQuantity.text,
            "Amount": "TO BE CONFIRMED" if float(self.txtSellingPrice.text) == 0 else f"{float(self.txtSellingPrice.text):,.2f}",
            "GroupID": self.txtGroupParts.text
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
        self.txtGroupParts.text=""
        self.lbl_ID.text=""
        self.lbl_PartName.text=""
        self.lbl_PartNumber.text=""
       

    def btn_AddServices_click(self, **event_args):
        """This method is called when the button is clicked"""
        textAmount = str(self.txtAmount.text).strip()
        
        if not self.txtServices.text:
            alert(
                "Sorry, please enter service name to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtServices.focus()
            return

        if textAmount == "":
            alert(
                "Sorry, please enter amount to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtAmount.focus()
            return
        if not self.txtGroupServices.text:
            alert(
                "Sorry, please enter group number to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtGroupServices.focus()
            return

        # Populate data grid with assigned parts
        new_service = {
            "Name": self.txtServices.text,
            "Amount": "TO BE CONFIRMED" if float(self.txtAmount.text) == 0 else f"{float(self.txtAmount.text):,.2f}",
            "GroupID":self.txtGroupServices.text
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
        self.txtGroupServices.text=""

    def btn_Save_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Save.enabled = False  # Prevent multiple clicks

        if not self.drop_down_select.selected_value:
            alert(
                "Sorry, please select Reg No to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.drop_down_select.focus()
            self.btn_Save.enabled = True
            return

        rows = self.repeating_panel_assigned_parts.items or []

        if not rows:
            anvil.alert(
                "Sorry, please assign parts or service to proceed.",
                title="Missing Assigned Parts or Service",
                large=False,
            )
            self.btn_Save.enabled = True
            return

        assignedDate = date.today()
        regNo = self.drop_down_select.selected_value

        batch_items = []
        for row in rows:
            raw_amt = str(row["Amount"])
            if raw_amt.upper() == "TO BE CONFIRMED":
                amount = 0.0
            else:
                amount = float(raw_amt.replace(",", "")) if "," in raw_amt else float(raw_amt)
            batch_items.append(
                {
                    "name": row["Name"],
                    "number": row.get("Number", ""),
                    "quantity": None if row.get("Quantity") is None else float(row["Quantity"]),
                    "amount": amount,
                    "groupid": row["GroupID"],
                }
            )

        anvil.server.call("save_brand_comparison_batch", assignedDate, regNo, batch_items)
        self._brand_cache.pop(regNo, None)

        Notification("Brand comparison saved successfully and download is initiated", title="Success", style="success", timeout=3).show()
        self.downloadBrandComparisonPdf(regNo)

        # Clear form
        self.clear_form_fields()      

    def downloadBrandComparisonPdf(self, regNo):
        media_object = anvil.server.call("downloadRevisionPdfForm", regNo, "Brand")
        anvil.media.download(media_object)
        self.deleteFile(regNo, "Brand")

    def deleteFile(self, regNo, docType):
        anvil.server.call("deleteRevisionFile", regNo, docType)

    def btn_DeleteRow_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.remove_from_parent()

    def btn_Download_click(self, **event_args):
        """This method is called when the button is clicked"""

        if not self.drop_down_select.selected_value:
            alert(
                "Sorry, please select Reg No to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.drop_down_select.focus()
            return

        elif self.drop_down_select.selected_value:
            existingData = anvil.server.call_s(
                "getBrandComparisonList", self.drop_down_select.selected_value
            )
            if existingData:
                self.downloadBrandComparisonPdf(self.drop_down_select.selected_value)
            else:
                alert(
                    "Sorry, there's no priority list found for the Reg No",
                    title="Missing Priority List",
                    large=False,
                )
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
        self.txtGroupParts.text = ""
        self.txtServices.text = ""
        self.txtAmount.text = ""
        self.txtGroupServices.text = ""
        self.repeating_panel_assigned_parts.items = []

        self.btn_Save.enabled = True