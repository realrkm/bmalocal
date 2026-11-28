from ._anvil_designer import AddNewPartsTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModGetData
from .. import ModCache


class AddNewParts(AddNewPartsTemplate):
    def __init__(self, isPopup=False, **properties):
        self.isPopup = isPopup
        self.init_components(**properties)
        self.data = {"locations": [], "suppliers": []}
        self._prewarmed_edit_modal = None
        self.set_event_handler("show", self._on_form_show)

        cached = ModCache.get_cached("locations_and_suppliers")
        if cached is not None:
            self._apply_lookups(cached)
        else:
            try:
                anvil.js.window.setTimeout(self._hydrate_lookups, 0)
            except Exception:
                self._hydrate_lookups()

        # Disable Close button when form appears under Inventory
        if self.isPopup is False:
            self.btn_Close.visible = False
            self.btn_Close.enabled = False
            self.btn_EditNewPart.visible = True
            self.btn_EditNewPart.enabled = True
        else:  # Display Close button and hide Edit button when form is called in MapBarcodePartNo as a popup
            self.btn_EditNewPart.visible = False
            self.btn_EditNewPart.enabled = False
            self.btn_Close.visible = True
            self.btn_Close.enabled = True

    def _apply_lookups(self, lookups):
        self.data = lookups or {"locations": [], "suppliers": []}
        self.drop_down_location.items = self.data.get("locations", [])
        self.drop_down_supplier.items = self.data.get("suppliers", [])

    def _hydrate_lookups(self):
        try:
            with anvil.server.no_loading_indicator:
                lookups = ModGetData.getLocationAndSupplier()
            self._apply_lookups(lookups)
        except Exception:
            pass

    def _prewarm_edit_modal(self):
        if self.isPopup or self._prewarmed_edit_modal is not None:
            return
        try:
            from ..EditAddNewParts import EditAddNewParts
            self._prewarmed_edit_modal = EditAddNewParts()
        except Exception:
            self._prewarmed_edit_modal = None

    def _on_form_show(self, **event_args):
        cached = ModCache.get_cached("locations_and_suppliers")
        if cached is not None and cached != self.data:
            self._apply_lookups(cached)
        if not self.isPopup and self._prewarmed_edit_modal is None:
            try:
                anvil.js.window.setTimeout(self._prewarm_edit_modal, 30)
            except Exception:
                pass

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_AddLocation_click(self, **event_args):
        """This method is called when the button is clicked"""
        from ..AddLocation import AddLocation
        alert(content=AddLocation(), buttons=[], dismissible=False, large=True)
        self._hydrate_lookups()

    def btn_AddSupplier_click(self, **event_args):
        """This method is called when the button is clicked"""
        from ..AddSupplier import AddSupplier
        alert(content=AddSupplier(), buttons=[], dismissible=False, large=True)
        self._hydrate_lookups()

    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_SaveAndNew.enabled = False
        
        purchaseDate = self.date_picker_purchase.date
        partName = self.txtPartName.text
        partNumber = self.txtPartNumber.text
        locationID = self.drop_down_location.selected_value
        supplierID= self.drop_down_supplier.selected_value
        units = self.txtNoOfUnits.text
        buyingPrice = self.txtBuyingPrice.text
        sellingPrice = self.txtSellingPrice.text
        discountPrice = self.txtSellingDiscountedPrice.text
        reorderLevel = self.txtReorderLevel.text

        if not purchaseDate:
            Notification("Sorry, please enter purchase date", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.date_picker_purchase.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not partName:
            Notification("Sorry, please enter car part name to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtPartName.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not partNumber:
            Notification("Sorry, please enter car part number to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtPartNumber.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not locationID:
            Notification("Sorry, please select storage location to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.drop_down_location.focus()
            self.btn_SaveAndNew.enabled = True
            return
            
        if not supplierID:
            Notification("Sorry, please select supplier to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.drop_down_supplier.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        if not units:
            Notification("Sorry, please enter number of units to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtNoOfUnits.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        if not buyingPrice:
            Notification("Sorry, please enter buying price to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtBuyingPrice.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        if not sellingPrice:
            Notification("Sorry, please enter selling price to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtSellingPrice.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        if not reorderLevel:
            Notification("Sorry, please enter reorder level to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtReorderLevel.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        #Avoid duplicate part number
        result = anvil.server.call("check_duplicate_number", self.txtPartNumber.text)

        if result:
            Notification("This part number is already in use. Please enter a unique part number.", title="Duplicate Part Number Found", style="warning", timeout=3).show()
            self.txtPartNumber.focus()
            self.btn_SaveAndNew.enabled = True
            return
            
        anvil.server.call_s("addNewParts", purchaseDate, partName, partNumber, locationID, supplierID, units, buyingPrice, sellingPrice,discountPrice, reorderLevel)
        #Update Blank Car Part Categories
        anvil.server.call_s("update_null_carpart_categories")
        Notification("Part Saved Successfully", title="Success", style="success", timeout=3).show()

        if self.isPopup is True:
            self.btn_Close_click()
        else:
            # Clear form
            self.clear_form_fields()       

    def btn_EditNewPart_click(self, **event_args):
        """Open pre-warmed EditAddNewParts modal immediately."""
        modal = self._prewarmed_edit_modal
        self._prewarmed_edit_modal = None
        if modal is None:
            from ..EditAddNewParts import EditAddNewParts
            modal = EditAddNewParts()
        alert(content=modal, buttons=[], dismissible=False, large=True)
        try:
            anvil.js.window.setTimeout(self._prewarm_edit_modal, 15)
        except Exception:
            pass

    def clear_form_fields(self):
        """Reset all form fields to blank/initial values"""
        self.date_picker_purchase.date = None
        self.txtPartName.text = ""
        self.txtPartNumber.text = ""
        self.drop_down_location.selected_value = None
        self.drop_down_supplier.selected_value = None
        self.txtNoOfUnits.text = ""
        self.txtBuyingPrice.text = ""
        self.txtSellingPrice.text = ""
        self.txtSellingDiscountedPrice.text = ""
        self.txtReorderLevel.text = ""
        self.drop_down_location.items = self.data.get("locations", [])
        self.drop_down_supplier.items = self.data.get("suppliers", [])
        self.refresh()
        self.btn_SaveAndNew.enabled = True

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value=True)

    def btn_ViewCarPartCategories_click(self, **event_args):
        """This method is called when the button is clicked"""
        from ..ViewAndUpdateCarPartCategoriesForTechnicianPortal import ViewAndUpdateCarPartCategoriesForTechnicianPortal
        alert(content=ViewAndUpdateCarPartCategoriesForTechnicianPortal(), buttons=[], dismissible=False, large=True)