from ._anvil_designer import UpdateBuyingAndSellingPriceTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class UpdateBuyingAndSellingPrice(UpdateBuyingAndSellingPriceTemplate):
    def __init__(self, items, priceType, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
              
        self.txt_Supplier.text = items["Supplier"]
        self.txt_PartName.text = items["Name"]
        self.txt_PartNo.text = items["PartNo"]
        
        if priceType == "Selling":
            self.label_title.text = "Update Selling Price"
            self.label_Price.text = "Selling Price"
            self.txt_Price.text = items["Amount"]
            self.txt_Discount.text = items["Discount"]
        else:
            self.label_title.text = "Update Buying Price"
            self.label_Price.text = "Buying Price"
            self.label_Discount.visible = False
            self.txt_Discount.visible=False
            self.txt_Price.text = items["Cost"]
            self.txt_Discount.visible =False

        self.txt_Price.focus()

    def btn_Update_click(self,  **event_args):
        """This method is called when the button is clicked"""
        price_text = self.txt_Price.text.replace(",", "").strip()
        
        if self.label_title.text == "Update Selling Price":
            priceType = "Selling"
            discount_text = self.txt_Discount.text.replace(",", "").strip()
            if not discount_text:
                discount_text = 0
                            
        else:
            priceType = "Buying"
        
        newPrice = float(price_text)
        partNo = self.txt_PartNo.text
    
        if newPrice  > 0:
            if priceType == "Selling":
                discount = float(discount_text)
                if discount >= newPrice:
<<<<<<< HEAD
                    alert("Sorry, discount should be less than selling price.", title="Mismatch Prices", large=False)
=======
                    Notification("Sorry, discount should be less than selling price.", title="Mismatch Prices", style="warning", timeout=3).show()
>>>>>>> origin/main
                    return
                else:
                    anvil.server.call_s("updatePrice", priceType, newPrice, discount, partNo)
            else:
                anvil.server.call_s("updatePrice", priceType, newPrice, 0, partNo)
                
<<<<<<< HEAD
            alert("Price Updated Successfully", title="Success", large=False)       
            self.btn_Close_click()
        else:
            alert("Sorry, please update the price to reflect the changes.")
=======
            Notification("Price Updated Successfully", title="Success", style="success", timeout=3).show()       
            self.btn_Close_click()
        else:
            Notification("Sorry, please update the price to reflect the changes.", style="warning", timeout=3).show()
>>>>>>> origin/main
        
    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)