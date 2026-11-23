from ._anvil_designer import StockBalanceTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js


class StockBalance(StockBalanceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self.data_grid_1.show_page_controls = True
        self._rt_token = None
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        self.repeating_panel_1.items = anvil.server.call("get_car_parts_summary", "")

    def form_show(self, **event_args):
        self.form_hide()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_token = rt.subscribe("inventory", self._on_inventory_changed)
        except Exception:
            pass

    def form_hide(self, **event_args):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt and self._rt_token:
                rt.unsubscribe(self._rt_token)
        except Exception:
            pass
        self._rt_token = None

    def _on_inventory_changed(self, evt=None):
        with anvil.server.no_loading_indicator:
            search_text = (self.text_box_search.text or "").strip()
            self.repeating_panel_1.items = anvil.server.call("get_car_parts_summary", search_text)

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_text = self.text_box_search.text.strip()

        if not search_text:
            alert(
                "Please enter part name or part number to search.",
                title="Missing Part Details",
            )
            self.text_box_search.focus()
            return

        result = anvil.server.call("get_car_parts_summary", search_text)

        if result:
            self.repeating_panel_1.items = ""
            self.repeating_panel_1.items = result
        else:
            Notification("No records found for the entered part detail.", title="Not Found", style="danger", timeout=3).show()

    def btn_Export_click(self, **event_args):
        rows = list(self.repeating_panel_1.items)

        if not rows:
            Notification("No data to export.", style="warning", timeout=3).show()
            return

        excel_file = anvil.server.call("export_stock_balance", rows)
        anvil.media.download(excel_file)

   