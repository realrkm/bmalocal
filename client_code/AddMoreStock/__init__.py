from ._anvil_designer import AddMoreStockTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModNavigation
from .. import ModGetData
from .. import ModCache
import re


class AddMoreStock(AddMoreStockTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        self._buying_prices_cache = {}
        self.set_event_handler("show", self._on_form_show)

        cached = ModCache.get_cached("locations_and_suppliers")
        if cached is not None:
            self.drop_down_selectSupplier.items = cached.get("suppliers", [])
        else:
            try:
                anvil.js.window.setTimeout(self._hydrate_suppliers, 0)
            except Exception:
                self._hydrate_suppliers()

    def _hydrate_suppliers(self):
        try:
            with anvil.server.no_loading_indicator:
                lookups = ModGetData.getLocationAndSupplier()
            self.drop_down_selectSupplier.items = (lookups or {}).get("suppliers", [])
        except Exception:
            pass

    def _on_form_show(self, **event_args):
        cached = ModCache.get_cached("locations_and_suppliers")
        if cached is not None:
            self.drop_down_selectSupplier.items = cached.get("suppliers", [])

    def _speculative_warm_buying_prices(self, part_id):
        if not part_id or part_id in self._buying_prices_cache:
            return
        try:
            with anvil.server.no_loading_indicator:
                self._buying_prices_cache[part_id] = anvil.server.call_s("get_buying_prices_by_partID", part_id)
        except Exception:
            pass

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

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
                anvil.js.window.setTimeout(lambda: self._speculative_warm_buying_prices(first_part_id), 0)
            except Exception:
                pass
        else:
            Notification("No records found for the entered part detail.", title="Not Found", style="danger", timeout=3).show()


    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_SaveAndNew.enabled = False  # Disable button to prevent multiple clicks

        additionDate = self.date_picker_1.date
        supplier = self.drop_down_selectSupplier.selected_value
        partID = self.drop_down_selectPart.selected_value
        no_of_units = self.txt_NoOfUnits.text
        unit_cost = self.txt_UnitCost.text

        if not additionDate:
            Notification("Please enter date to proceed.", style="warning", timeout=3).show()
            self.date_picker_1.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not supplier:
            Notification("Please select supplier to proceed.", style="warning", timeout=3).show()
            self.drop_down_selectSupplier.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not no_of_units:
            Notification("Please enter number of units to proceed.", style="warning", timeout=3).show()
            self.txt_NoOfUnits.focus()
            self.btn_SaveAndNew.enabled = True
            return

        if not unit_cost:
            Notification("Please enter unit cost to proceed.", style="warning", timeout=3).show()
            self.txt_UnitCost.focus()
            self.btn_SaveAndNew.enabled = True
            return

        # Save data
        anvil.server.call("addStock", additionDate, supplier, partID, no_of_units, unit_cost)
        self._buying_prices_cache.pop(partID, None)
        Notification("Stock added successfully.", style="warning", timeout=3).show()

        # Clear form
        self.clear_form_fields()

    def drop_down_selectPart_change(self, **event_args):
        """This method is called when an item is selected"""
        part_id = self.drop_down_selectPart.selected_value
        if not part_id:
            self.repeating_panel_1.items = []
            return
        if part_id in self._buying_prices_cache:
            result = self._buying_prices_cache[part_id]
        else:
            result = anvil.server.call("get_buying_prices_by_partID", part_id)
            self._buying_prices_cache[part_id] = result

        if result:
            self.repeating_panel_1.items = ""
            self.repeating_panel_1.items = result
        else:
            Notification("No records found for the entered part detail.", title="Not Found", style="danger", timeout=3).show()

    def clear_form_fields(self):
        """Reset all fields after saving"""
        self.date_picker_1.date = None
        self.text_box_searchPartNo.text = ""
        self.drop_down_selectPart.items = []
        self.drop_down_selectPart.selected_value = None
        self.txt_NoOfUnits.text = ""
        self.txt_UnitCost.text = ""
        self.repeating_panel_1.items = []
        lookups = ModGetData.getLocationAndSupplier()
        self.drop_down_selectSupplier.items = (lookups or {}).get("suppliers", [])
        self.drop_down_selectSupplier.selected_value = None
        # Put cursor back on search box for next entry
        self.text_box_searchPartNo.focus()

        self.refresh()
        self.btn_SaveAndNew.enabled = True

   