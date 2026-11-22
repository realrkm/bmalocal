from ._anvil_designer import StockBalanceTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModPagination


class StockBalance(StockBalanceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self._page_size = 50
        self._offset = 0
        self._total = 0
        self._search_text = ""
        self._rt_token = None
        self._pagination_bar = ModPagination.create_pagination_bar(self._prev_page, self._next_page)
        self.card_2.add_component(self._pagination_bar["panel"], full_width_row=True)
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)
        
        self._load_page()

    def _prev_page(self):
        if self._offset >= self._page_size:
            self._offset -= self._page_size
            self._load_page()

    def _next_page(self):
        if self._offset + self._page_size < self._total:
            self._offset += self._page_size
            self._load_page()

    def _load_page(self):
        page = anvil.server.call("get_car_parts_summary_paginated", self._search_text, self._page_size, self._offset)
        self._total = page.get("total", 0)
        self.repeating_panel_1.items = page.get("items", [])
        ModPagination.update_pagination_bar(self._pagination_bar, self._offset, self._page_size, self._total)
        return self.repeating_panel_1.items

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
            self._load_page()
       
        
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

        self._search_text = search_text
        self._offset = 0
        result = self._load_page()

        if not result:
            Notification("No records found for the entered part detail.", title="Not Found", style="danger", timeout=3).show()

    def btn_Export_click(self, **event_args):
        rows = list(self.repeating_panel_1.items)

        if not rows:
            Notification("No data to export.", style="warning", timeout=3).show()
            return

        excel_file = anvil.server.call("export_stock_balance", rows)
        anvil.media.download(excel_file)

   