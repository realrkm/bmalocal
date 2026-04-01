from ._anvil_designer import PriceCatalogueTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..BuyingPrice import BuyingPrice
from ..MissingBuyingPrice import MissingBuyingPrice
from ..SellingPrice import SellingPrice
from ..MissingSellingPrice import MissingSellingPrice
import anvil.js

class PriceCatalogue(PriceCatalogueTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        
        self.repeating_panel_1.items = anvil.server.call("get_filtered_parts")
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_text = self.text_box_search.text.strip()

        if not search_text:
            alert("Please enter part name or part number to search.", title="Missing Part Details")
            self.text_box_search.focus()
            return

        result = anvil.server.call("get_filtered_parts", search_text)

        if result:
            # Clear drop down
            self.repeating_panel_1.items = ""
            self.repeating_panel_1.items = result
        else:
            alert("No records found for the entered part detail.", title="Not Found")

    def btn_BuyingPrice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_BuyingPrice.enabled = False
        alert(content=BuyingPrice(), buttons=[], dismissible=False,large=True)
        self.btn_BuyingPrice.enabled = True

    def btn_SellingPrice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_SellingPrice.enabled = False
        alert(content=SellingPrice(), buttons=[], dismissible=False,large=True)
        self.btn_SellingPrice.enabled = True
        
    def btn_MissingBuyingPrice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_MissingBuyingPrice.enabled = False
        alert(content=MissingBuyingPrice(), buttons=[], dismissible=False,large=True)
        self.btn_MissingBuyingPrice.enabled = True
        
    def btn_MissingSellingPrice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_MissingSellingPrice.enabled = False
        alert(content=MissingSellingPrice(), buttons=[], dismissible=False,large=True)
        self.btn_MissingSellingPrice.enabled = True

   
    def btn_Export_click(self, **event_args):
        """This method is called when the button is clicked"""
        excel_file = anvil.server.call("export_current_selling_prices_and_reorder_levels")
        anvil.media.download(excel_file)
        alert("Selling Prices and Reorder Levels exported successfully.", title="Success", large=False)


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
            self.file_uploader_1.clear()
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
            self.file_uploader_1.clear()
            return

        # Show progress while processing
        with anvil.server.no_loading_indicator:
            Notification(
                "Importing data, please wait...",
                title="Processing",
                style="info",
                timeout=None
            ).show()

        try:
            summary = anvil.server.call(
                "import_selling_prices_and_reorder_levels", file
            )
            # Check if any rows were skipped
            if "skipped" in summary.lower():
                alert(
                    summary,
                    title="Import Completed with Warnings",
                    large=True
                )
            else:
                alert(
                    summary,
                    title="Import Successful",
                    large=False
                )
        except Exception as e:
            alert(
                f"An error occurred during import:\n\n{str(e)}",
                title="Import Failed",
                large=True
            )
        finally:
            self.file_uploader_1.clear()

    