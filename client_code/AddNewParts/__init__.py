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


class AddNewParts(AddNewPartsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        self.drop_down_location.items = anvil.server.call("getLocation")
        self.drop_down_supplier.items = anvil.server.call("getSupplier")
        
    def btn_AddLocation_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=AddLocation(), buttons=[], dismissible=False, large=True)

    def btn_AddSupplier_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=AddSupplier(), buttons=[], dismissible=False, large=True)


    def btn_SaveAndDownload_click(self, **event_args):
        """This method is called when the button is clicked"""
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
            return

        if not partName:
            alert("Sorry, please enter car part name to proceed", title="Blank Field(s) Found", large=False)
            self.txtPartName.focus()
            return

        if not partNumber:
            alert("Sorry, please enter car part number to proceed", title="Blank Field(s) Found", large=False)
            self.txtPartNumber.focus()
            return

        if not locationID:
            alert("Sorry, please select storage location to proceed", title="Blank Field(s) Found", large=False)
            self.drop_down_location.focus()
            return
            
        if not supplierID:
            alert("Sorry, please select supplier to proceed", title="Blank Field(s) Found", large=False)
            self.drop_down_supplier.focus()
            return    

        if not units:
            alert("Sorry, please enter number of units to proceed", title="Blank Field(s) Found", large=False)
            self.txtNoOfUnits.focus()
            return    

        if not buyingPrice:
            alert("Sorry, please enter buying price to proceed", title="Blank Field(s) Found", large=False)
            self.txtBuyingPrice.focus()
            return    

        if not sellingPrice:
            alert("Sorry, please enter selling price to proceed", title="Blank Field(s) Found", large=False)
            self.txtSellingPrice.focus()
            return    

        if not reorderLevel:
            alert("Sorry, please enter reorder level to proceed", title="Blank Field(s) Found", large=False)
            self.txtReorderLevel.focus()
            return    

        #Avoid duplicate part number
        result = anvil.server.call("check_duplicate_number", self.txtPartNumber.text)

        if result:
            alert("This part number is already in use. Please enter a unique part number.", title="Duplicate Part Number Found", large=False)
            self.txtPartNumber.focus()
            return
            
        anvil.server.call_s("addNewParts", purchaseDate, partName, partNumber, locationID, supplierID, units, buyingPrice, sellingPrice,discountPrice, reorderLevel)
        alert("Part Saved Successfully", title="Success", large=False)
        get_open_form().btn_Inventory_click("AddNewParts")

    def btn_EditNewPart_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=EditAddNewParts(), buttons=[], dismissible=False, large=True)
