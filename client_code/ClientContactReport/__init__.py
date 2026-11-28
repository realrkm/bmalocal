from ._anvil_designer import ClientContactReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


class ClientContactReport(ClientContactReportTemplate):
    def __init__(self, clientID=None, **properties):
        self.init_components(**properties)
        self.client_id = clientID
        self.data_grid_1.show_page_controls = True
        self._rt_token = None
        self._is_mounted = True
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekClientReportCached", lambda: None)()
        if cached is not None:
            self._apply_cached_rows(cached, clientID)
        else:
            anvil.js.window.setTimeout(self._load_initial_data, 0)

    def _apply_cached_rows(self, rows, client_id):
        if client_id is None:
            self.client_repeater.items = rows
        else:
            self.client_repeater.items = [
                {**r, "No": idx}
                for idx, r in enumerate((r for r in rows if r.get("ID") == client_id), start=1)
            ]

    def set_filter(self, clientID):
        """Filter in-place in 0ms when cache is warm, avoiding full form reconstruction."""
        if self.client_id == clientID and self.client_repeater.items:
            return
        self.client_id = clientID
        cached = getattr(ModGetData, "peekClientReportCached", lambda: None)()
        if cached is not None:
            self._apply_cached_rows(cached, clientID)
            return
        with anvil.server.no_loading_indicator:
            self.refresh_client_table(clientID)

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
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
            self.refresh_client_table(self.client_id, force_refresh=True)

    def refresh_client_table(self, clientID, force_refresh=False):
        if clientID is None and hasattr(ModGetData, "getClientReportCached"):
            clients = ModGetData.getClientReportCached(force_refresh=force_refresh)
        elif hasattr(ModGetData, "getClientReportCached"):
            all_clients = ModGetData.getClientReportCached(force_refresh=force_refresh)
            if all_clients is not None:
                self._apply_cached_rows(all_clients, clientID)
                return
            clients = anvil.server.call('getClientReport', clientID)
        else:
            clients = anvil.server.call('getClientReport', clientID)
        self.client_repeater.items = clients
            
       