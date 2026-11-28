from ._anvil_designer import CarDetailsReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


class CarDetailsReport(CarDetailsReportTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._is_mounted = True
        self._rt_token = None
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekCarDetailsCached", lambda: None)()
        if cached is not None:
            self.car_repeater.items = cached
        else:
            anvil.js.window.setTimeout(self._load_initial_data, 0)

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
                self._rt_token = rt.subscribe("jobcards", self._on_jobcards_changed)
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._is_mounted = False
        self._unsubscribe_realtime()

    def _on_jobcards_changed(self, evt=None):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            search_term = (self.txt_Search.text or "").strip()
            part_name = (self.txt_PartName.text or "").strip()
            if not search_term and not part_name:
                if hasattr(ModGetData, "getCarDetailsCached"):
                    rows = ModGetData.getCarDetailsCached(force_refresh=True)
                else:
                    rows = anvil.server.call("get_car_details", None)
            elif search_term and not part_name:
                rows = anvil.server.call("get_car_details", search_term)
            else:
                rows = anvil.server.call("get_car_details_and_parts", search_term, part_name)
        if self._is_mounted:
            self.car_repeater.items = rows or []

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            if hasattr(ModGetData, "getCarDetailsCached"):
                rows = ModGetData.getCarDetailsCached()
            else:
                rows = anvil.server.call("get_car_details", None)
        if self._is_mounted:
            self.car_repeater.items = rows
        
    def btn_Search_click(self, **event_args):
        """This method is called when the button is clicked"""
        search_term = self.txt_Search.text.strip()
        part_name=self.txt_PartName.text.strip()

        # 1. No filters selected
        if not search_term and not part_name:
            Notification("Sorry, please enter keyword, part name or both to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            return
        elif search_term and not part_name:
            cardetails = anvil.server.call('get_car_details', search_term)
        else:
            cardetails = anvil.server.call("get_car_details_and_parts", search_term, part_name)
                       
        
        if cardetails:
            self.car_repeater.items = cardetails
        else:
            Notification("No records found for the entered keyword and or part name.", title="Not Found", style="danger", timeout=3).show()
