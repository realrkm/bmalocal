from ._anvil_designer import EditAddNewPartsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..AddLocation import AddLocation
from ..AddSupplier import AddSupplier
import anvil.js


class EditAddNewParts(EditAddNewPartsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.drop_down_location.items = anvil.server.call("getLocation")
        self.drop_down_supplier.items = anvil.server.call("getSupplier")


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

        stockParts = anvil.server.call("getPartsDetailsID", self.lbl_ID.text)
        self.lbl_SupplierId.text = stockParts["CarPartsSupplierID"]
        sellingDetails = anvil.server.call("getPartsSellingDetailsID", self.lbl_ID.text)

        #Populate form
        self.date_picker_purchase.date = stockParts["Date"]
        self.txtPartName.text =  stockParts["Name"]
        self.txtPartNumber.text =  stockParts["PartNo"]

        self.drop_down_location.selected_value = stockParts["Location"]
        self.drop_down_supplier.selected_value = stockParts["CarPartsSupplierID"]

        self.txtNoOfUnits.text =   stockParts["NoOfUnits"]
        self.txtBuyingPrice.text =  stockParts["UnitCost"]

        if sellingDetails is not None:
            self.txtSellingPrice.text = sellingDetails["Amount"]
            self.txtSellingDiscountedPrice.text = sellingDetails["SaleDiscount"]
        elif sellingDetails is None:
            self.txtSellingPrice.text = 0
            self.txtSellingDiscountedPrice.text = 0

        self.txtReorderLevel.text = stockParts["OrderLevel"]

    
    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        purchaseDate = self.date_picker_purchase.date
        partName = self.txtPartName.text
        partNumber = self.txtPartNumber.text
        locationID = self.drop_down_location.selected_value
        supplierID = self.drop_down_supplier.selected_value
        units = self.txtNoOfUnits.text
        buyingPrice = self.txtBuyingPrice.text
        sellingPrice = self.txtSellingPrice.text
        discountPrice = self.txtSellingDiscountedPrice.text
        reorderLevel = self.txtReorderLevel.text

        if not purchaseDate:
            alert(
                "Sorry, please enter purchase date",
                title="Blank Field(s) Found",
                large=False,
            )
            self.date_picker_purchase.focus()
            return

        if not partName:
            alert(
                "Sorry, please enter car part name to proceed",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtPartName.focus()
            return

        if not partNumber:
            alert(
                "Sorry, please enter car part number to proceed",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtPartNumber.focus()
            return

        if not locationID:
            alert(
                "Sorry, please select storage location to proceed",
                title="Blank Field(s) Found",
                large=False,
            )
            self.drop_down_location.focus()
            return

        if not supplierID:
            alert(
                "Sorry, please select supplier to proceed",
                title="Blank Field(s) Found",
                large=False,
            )
            self.drop_down_supplier.focus()
            return

        if not units:
            alert(
                "Sorry, please enter number of units to proceed",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtNoOfUnits.focus()
            return

        if not buyingPrice:
            alert(
                "Sorry, please enter buying price to proceed",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtBuyingPrice.focus()
            return

        if not sellingPrice:
            alert(
                "Sorry, please enter selling price to proceed",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtSellingPrice.focus()
            return

        if not reorderLevel:
            alert(
                "Sorry, please enter reorder level to proceed",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtReorderLevel.focus()
            return

        anvil.server.call_s(
            "updateNewParts",
            purchaseDate,
            partName,
            partNumber,
            locationID,
            supplierID,
            units,
            buyingPrice,
            sellingPrice,
            discountPrice,
            reorderLevel,
            self.lbl_ID.text,
            self.lbl_SupplierId.text
        )
        alert("Part Updated Successfully", title="Success", large=False)
        self.btn_Close_click()


    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)


   
  