from ._anvil_designer import PriceCatalogueTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModGetData


class PriceCatalogue(PriceCatalogueTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self.data_grid_1.show_page_controls = True
        self.data_grid_1.role = 'wide'
        self._rt_token = None
        self._is_mounted = True
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekPriceCatalogueCached", lambda: None)()
        if cached is not None:
            self.repeating_panel_1.items = cached
        else:
            anvil.js.window.setTimeout(self._load_initial_data, 0)

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            if hasattr(ModGetData, "getPriceCatalogueCached"):
                rows = ModGetData.getPriceCatalogueCached()
            else:
                rows = anvil.server.call("get_filtered_parts")
        if self._is_mounted:
            self.repeating_panel_1.items = rows

    def _unsubscribe_realtime(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt and self._rt_token:
                rt.unsubscribe(self._rt_token)
        except Exception:
            pass
        self._rt_token = None

    def form_show(self, **event_args):
        self._is_mounted = True
        self._unsubscribe_realtime()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_token = rt.subscribe("inventory", self._on_inventory_changed)
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._is_mounted = False
        self._unsubscribe_realtime()

    def _on_inventory_changed(self, evt=None):
        with anvil.server.no_loading_indicator:
            search_text = (self.text_box_search.text or "").strip()
            if search_text:
                self.repeating_panel_1.items = anvil.server.call("get_filtered_parts", search_text)
            elif hasattr(ModGetData, "getPriceCatalogueCached"):
                self.repeating_panel_1.items = ModGetData.getPriceCatalogueCached(force_refresh=True)
            else:
                self.repeating_panel_1.items = anvil.server.call("get_filtered_parts")

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_text = self.text_box_search.text.strip()

        if not search_text:
            Notification("Please enter part name or part number to search.", title="Missing Part Details", style="danger", timeout=3).show()
            self.text_box_search.focus()
            return

        result = anvil.server.call("get_filtered_parts", search_text)

        if result:
            self.repeating_panel_1.items = ""
            self.repeating_panel_1.items = result
        else:
            Notification("No records found for the entered part detail.", title="Not Found", style="danger", timeout=3).show()

    def btn_BuyingPrice_click(self, **event_args):
        from ..BuyingPrice import BuyingPrice
        self.btn_BuyingPrice.enabled = False
        alert(content=BuyingPrice(), buttons=[], dismissible=False, large=True)
        self.btn_BuyingPrice.enabled = True

    def btn_SellingPrice_click(self, **event_args):
        from ..SellingPrice import SellingPrice
        self.btn_SellingPrice.enabled = False
        alert(content=SellingPrice(), buttons=[], dismissible=False, large=True)
        self.btn_SellingPrice.enabled = True

    def btn_MissingBuyingPrice_click(self, **event_args):
        from ..MissingBuyingPrice import MissingBuyingPrice
        self.btn_MissingBuyingPrice.enabled = False
        alert(content=MissingBuyingPrice(), buttons=[], dismissible=False, large=True)
        self.btn_MissingBuyingPrice.enabled = True

    def btn_MissingSellingPrice_click(self, **event_args):
        from ..MissingSellingPrice import MissingSellingPrice
        self.btn_MissingSellingPrice.enabled = False
        alert(content=MissingSellingPrice(), buttons=[], dismissible=False, large=True)
        self.btn_MissingSellingPrice.enabled = True

   
    def btn_Export_click(self, **event_args):
        """This method is called when the button is clicked"""
        excel_file = anvil.server.call("export_current_selling_prices_and_reorder_levels")
        anvil.media.download(excel_file)
        Notification("Selling Prices and Reorder Levels exported successfully.", title="Success", style="success", timeout=3).show()


    def _reset_file_uploader(self):
        """Resets the file uploader using the built-in clear method."""
        self.file_loader_import.clear()

    def file_loader_import_change(self, file, **event_args):
        """This method is called when a new file is selected for upload."""
        if file is None:
            return

        # Validate file type
        if not file.name.endswith(".xlsx"):
            alert(
                "Invalid file type. Please upload a valid Excel (.xlsx) file.",
                title="Invalid File",
                large=False
            )
            self._reset_file_uploader()  #  Clear after wrong file type alert is dismissed
            return

        # Confirm before proceeding
        confirmed = confirm(
            f"You are about to import '{file.name}'. "
            "This will update selling prices, discount prices, and reorder levels in the database. "
            "Do you want to proceed?",
            title="Confirm Import",
            buttons=[("Yes, Import", True), ("Cancel", False)]
        )
        if not confirmed:
            self._reset_file_uploader()  # Clear on cancel
            return

        # Show progress notification and keep a reference to dismiss it later
        notification = Notification(
            "Importing data, please wait...",
            title="Processing",
            style="info",
            timeout=None
        )
        notification.show()

        try:
            summary = anvil.server.call(
                "import_selling_prices_and_reorder_levels", file
            )
            if "skipped" in summary.lower():
                alert(summary, title="Import Completed with Warnings", large=True)
            else:
                alert(summary, title="Import Successful", large=False)
        except Exception as e:
            alert(
                f"An error occurred during import:\n\n{str(e)}",
                title="Import Failed",
                large=True
            )
        finally:
            notification.hide()           # Dismiss notification when processing is done
            self._reset_file_uploader()   # Clear after processing completes
        if hasattr(ModGetData, "getPriceCatalogueCached"):
            self.repeating_panel_1.items = ModGetData.getPriceCatalogueCached(force_refresh=True)
        else:
            self.repeating_panel_1.items = anvil.server.call("get_filtered_parts")