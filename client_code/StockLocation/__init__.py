from ._anvil_designer import StockLocationTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


class StockLocation(StockLocationTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._rt_token = None
        self._is_mounted = True
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekStockLocationCached", lambda: None)()
        if cached is not None:
            self.repeating_panel_1.items = cached
        else:
            anvil.js.window.setTimeout(self._load_initial_data, 0)

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            if hasattr(ModGetData, "getStockLocationCached"):
                rows = ModGetData.getStockLocationCached()
            else:
                rows = anvil.server.call("search_car_parts_location")
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
                self.repeating_panel_1.items = anvil.server.call("search_car_parts_location", search_text)
            elif hasattr(ModGetData, "getStockLocationCached"):
                self.repeating_panel_1.items = ModGetData.getStockLocationCached(force_refresh=True)
            else:
                self.repeating_panel_1.items = anvil.server.call("search_car_parts_location")

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_text = self.text_box_search.text.strip()

        if not search_text:
            Notification("Please enter location or part name or part number to search.", title="Missing Location / Part Details", style="danger", timeout=3).show()
            self.text_box_search.focus()
            return

        result = anvil.server.call(
            "search_car_parts_location", search_text)

        if result:
            # Clear drop down
            self.repeating_panel_1.items = ""
            self.repeating_panel_1.items = result
        else:
            Notification("No records found for the entered part detail.", title="Not Found", style="danger", timeout=3).show()

       
