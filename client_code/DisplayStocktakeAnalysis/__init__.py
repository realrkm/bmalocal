from ._anvil_designer import DisplayStocktakeAnalysisTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class DisplayStocktakeAnalysis(DisplayStocktakeAnalysisTemplate):
    def __init__(self, start_date=None, end_date=None, partnumber=None,**properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call("replaceBanner")
        self._start_date = start_date
        self._end_date = end_date
        self._partnumber = partnumber
        self._rt_token = None
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)
        
        self.html = anvil.server.call("get_stock_analysis_report", start_date=start_date, end_date=end_date, partnumber=partnumber)

    def _unsubscribe_realtime(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt and self._rt_token:
                rt.unsubscribe(self._rt_token)
        except Exception:
            pass
        self._rt_token = None

    def form_show(self, **event_args):
        self._unsubscribe_realtime()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_token = rt.subscribe("inventory", self._on_inventory_changed)
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._unsubscribe_realtime()

    def _on_inventory_changed(self, evt=None):
        with anvil.server.no_loading_indicator:
            self.html = anvil.server.call(
                "get_stock_analysis_report",
                start_date=self._start_date,
                end_date=self._end_date,
                partnumber=self._partnumber,
            )
