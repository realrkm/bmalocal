from ._anvil_designer import AddNewPartsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..AddLocation import AddLocation
from ..AddSupplier import AddSupplier
from ..EditAddNewParts import EditAddNewParts
import anvil.js

class AddNewParts(AddNewPartsTemplate):
    def __init__(self, isPopup= False, **properties):

        self.isPopup = isPopup #Instance variable, hence available in other methods
        
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
            
        # Any code you write here will run before the form opens.
        self.drop_down_location.items = anvil.server.call("getLocation")
        self.drop_down_supplier.items = anvil.server.call("getSupplier")

        # Disable Close button when form appears under Inventory
        if self.isPopup is False:
            self.btn_Close.visible = False
            self.btn_Close.enabled=False
            self.btn_EditNewPart.visible=True
            self.btn_EditNewPart.enabled = True
        else: #Display Close button and hide Edit button when form is called in MapBarcodePartNo as a popup 
            self.btn_EditNewPart.visible=False
            self.btn_EditNewPart.enabled = False
            self.btn_Close.visible = True
            self.btn_Close.enabled= True
            
    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)
        
    def btn_AddLocation_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=AddLocation(), buttons=[], dismissible=False, large=True)

    def btn_AddSupplier_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=AddSupplier(), buttons=[], dismissible=False, large=True)

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
            alert("Sorry, please enter purchase date", title="Blank Field(s) Found", large=False)
            self.date_picker_purchase.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not partName:
            alert("Sorry, please enter car part name to proceed", title="Blank Field(s) Found", large=False)
            self.txtPartName.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not partNumber:
            alert("Sorry, please enter car part number to proceed", title="Blank Field(s) Found", large=False)
            self.txtPartNumber.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not locationID:
            alert("Sorry, please select storage location to proceed", title="Blank Field(s) Found", large=False)
            self.drop_down_location.focus()
            self.btn_SaveAndNew.enabled = True
            return
            
        if not supplierID:
            alert("Sorry, please select supplier to proceed", title="Blank Field(s) Found", large=False)
            self.drop_down_supplier.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        if not units:
            alert("Sorry, please enter number of units to proceed", title="Blank Field(s) Found", large=False)
            self.txtNoOfUnits.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        if not buyingPrice:
            alert("Sorry, please enter buying price to proceed", title="Blank Field(s) Found", large=False)
            self.txtBuyingPrice.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        if not sellingPrice:
            alert("Sorry, please enter selling price to proceed", title="Blank Field(s) Found", large=False)
            self.txtSellingPrice.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        if not reorderLevel:
            alert("Sorry, please enter reorder level to proceed", title="Blank Field(s) Found", large=False)
            self.txtReorderLevel.focus()
            self.btn_SaveAndNew.enabled = True
            return    

        #Avoid duplicate part number
        result = anvil.server.call("check_duplicate_number", self.txtPartNumber.text)

        if result:
            alert("This part number is already in use. Please enter a unique part number.", title="Duplicate Part Number Found", large=False)
            self.txtPartNumber.focus()
            self.btn_SaveAndNew.enabled = True
            return
            
        anvil.server.call_s("addNewParts", purchaseDate, partName, partNumber, locationID, supplierID, units, buyingPrice, sellingPrice,discountPrice, reorderLevel)
        alert("Part Saved Successfully", title="Success", large=False)

        if self.isPopup is True:
            self.btn_Close_click()
        else:
            # Clear form
            self.clear_form_fields()       

    def btn_EditNewPart_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=EditAddNewParts(), buttons=[], dismissible=False, large=True)

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
        self.drop_down_location.items = anvil.server.call("getLocation")
        self.drop_down_supplier.items = anvil.server.call("getSupplier")
        self.refresh()
        self.btn_SaveAndNew.enabled = True

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)
