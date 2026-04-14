from ._anvil_designer import UpdateOrderTrackingTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class UpdateOrderTracking(UpdateOrderTrackingTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def btn_SearchClient_click(self, **event_args):
        """This method is called when the button is clicked"""
        searchTerm = self.text_box_searchPartNo.text

        if not searchTerm:
            alert("Please enter search term to proceed")
            self.text_box_searchPartNo.focus()
            return
        else:
            result = anvil.server.call("search_client_import_orders", searchTerm)

        if not result:
            alert("Sorry, no record was found matching the search term")
            self.text_box_searchPartNo.focus()
            return
        else:
            self.drop_down_selectDetails.items = result

    def drop_down_selectDetails_change(self, **event_args):
        """This method is called when an item is selected"""
        val = self.drop_down_selectDetails.selected_value  # {"client_id": ..., "order_date": ...}
        orders = anvil.server.call(
            'get_import_orders_for_selection',
            val["client_id"],
            val["order_date"]
        )
        self.repeating_panel_1.items = orders

    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Update.enabled = True
    
        val = self.drop_down_selectDetails.selected_value
        if not val:
            alert("Sorry, please select client to proceed")
            self.text_box_searchPartNo.focus()
            self.btn_Update.enabled = True
            return
        else:
            rows = self.repeating_panel_1.items
            items = []
            for row in rows:
                item_name = row.get('Name', '')
                part_no = row.get('Part_No', "")
                quantity = float(row["Quantity"]) if row.get("Quantity") not in (None, "") else None
    
                # --- Safe handling of Amount ---
                raw_amount = row.get("Amount", None)
                if raw_amount is None or raw_amount == "":
                    amount = None
                else:
                    amount_str = str(raw_amount)
                    amount = float(amount_str.replace(",", ""))
    
                status = row.get("Status", "")   # fixed row.get["Status"] -> row.get("Status")
    
                items.append({
                    "name": item_name,
                    "number": part_no,
                    "quantity": quantity,
                    "amount": amount,
                    "status": status
                })
  
        anvil.server.call("updateImportOrderTracking", val["order_date"], val["client_id"],  items)
        alert("Import order updated successfully", title="Success")
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)