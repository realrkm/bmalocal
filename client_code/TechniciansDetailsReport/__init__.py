from ._anvil_designer import TechniciansDetailsReportTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModGetData


class TechniciansDetailsReport(TechniciansDetailsReportTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._rt_token = None
        self._is_mounted = True
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekTechnicianReportCached", lambda: None)()
        if cached is not None:
            self.client_repeater.items = cached
        else:
            anvil.js.window.setTimeout(self._load_initial_data, 0)

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            self.refresh_technician_table()

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
            search_term = (self.txt_Search.text or "").strip()
            if search_term:
                self.client_repeater.items = anvil.server.call("getTechnicianReport", search_term)
            else:
                self.refresh_technician_table(force_refresh=True)

    def refresh_technician_table(self, force_refresh=False):
        if hasattr(ModGetData, "getTechnicianReportCached"):
            technicians = ModGetData.getTechnicianReportCached(force_refresh=force_refresh)
        else:
            technicians = anvil.server.call('getTechnicianReport', None)
        self.client_repeater.items = technicians

    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_term = self.txt_Search.text.strip()

        if not search_term:
            Notification("Please enter technician's name to search.", title="Missing Search Term", style="danger", timeout=3).show()
            self.txt_Search.focus()
            return

        cardetails = anvil.server.call("getTechnicianReport", search_term)

        if cardetails:
            self.client_repeater.items = cardetails
        else:
            Notification("No records found for the entered technician's name.", title="Not Found", style="danger", timeout=3).show()
