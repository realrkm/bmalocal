from ._anvil_designer import ClientContactReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModPagination

class ClientContactReport(ClientContactReportTemplate):
    def __init__(self, clientID, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        self.client_id = clientID
        self._page_size = 50
        self.data_grid_1.rows_per_page = self._page_size
        self.data_grid_1.show_page_controls = False
        self._offset = 0
        self._total = 0
        self._rt_token = None
        self._pagination_bar = ModPagination.create_pagination_bar(self._prev_page, self._next_page)
        self.add_component(self._pagination_bar["panel"])
        self._is_mounted = True
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)
        anvil.js.window.setTimeout(self._load_initial_data, 10)

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            self.refresh_client_table(self.client_id)

    def _prev_page(self):
        if self._offset >= self._page_size:
            self._offset -= self._page_size
            self.refresh_client_table(self.client_id)

    def _next_page(self):
        if self._offset + self._page_size < self._total:
            self._offset += self._page_size
            self.refresh_client_table(self.client_id)

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
                self._rt_token = rt.subscribe("contacts", self._on_contacts_changed)
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._is_mounted = False
        self._unsubscribe_realtime()

    def _on_contacts_changed(self, evt=None):
        with anvil.server.no_loading_indicator:
            self.refresh_client_table(self.client_id)

    def refresh_client_table(self, clientID):
        page = anvil.server.call('get_client_report_paginated', clientID, self._page_size, self._offset)
        self._total = page.get("total", 0)
        self.client_repeater.items = page.get("items", [])
        ModPagination.update_pagination_bar(self._pagination_bar, self._offset, self._page_size, self._total)
            
       