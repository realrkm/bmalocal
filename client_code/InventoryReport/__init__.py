from ._anvil_designer import InventoryReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class InventoryReport(InventoryReportTemplate):
    _ALL_TABS = (
        "PRICE CATALOGUE",
        "STOCK LOCATION",
        "STOCK BALANCE",
        "STOCK ANALYSIS",
        "CAR PARTS USED",
    )

    def __init__(self, buttonName="Catalogue", **properties):
        self.init_components(**properties)
        self._subforms = {}
        self._active_key = None
        self._prewarm_scheduled = False
        self._attach_hover_prewarm()
        self.set_event_handler("show", self.form_show)
        self.show_clicked_button(buttonName)

    def _build_subform(self, key):
        if key == "PRICE CATALOGUE":
            from ..PriceCatalogue import PriceCatalogue
            return PriceCatalogue()
        if key == "STOCK LOCATION":
            from ..StockLocation import StockLocation
            return StockLocation()
        if key == "STOCK BALANCE":
            from ..StockBalance import StockBalance
            return StockBalance()
        if key == "STOCK ANALYSIS":
            from ..StocktakeAnalysis import StocktakeAnalysis
            return StocktakeAnalysis()
        if key == "CAR PARTS USED":
            from ..CarPartsUsed import CarPartsUsed
            return CarPartsUsed()
        return None

    def _get_or_create_subform(self, key):
        subforms = getattr(self, "_subforms", None)
        if subforms is None:
            self._subforms = subforms = {}
        inst = subforms.get(key)
        if inst is None:
            inst = self._build_subform(key)
            if inst is not None:
                subforms[key] = inst
        return inst

    def _prewarm_single_subform(self, key):
        subforms = getattr(self, "_subforms", None)
        if subforms is not None and key in subforms:
            return
        try:
            self._get_or_create_subform(key)
        except Exception:
            pass

    def _attach_hover_prewarm(self):
        get_dom = getattr(anvil.js, "get_dom_node", None)
        if not callable(get_dom):
            return
        for attr, key in (
            ("btn_PriceCatalogue", "PRICE CATALOGUE"),
            ("btn_Location", "STOCK LOCATION"),
            ("btn_StockBalance", "STOCK BALANCE"),
            ("btn_StocktakeAnalysis", "STOCK ANALYSIS"),
            ("btn_CarPartsUsed", "CAR PARTS USED"),
        ):
            btn = getattr(self, attr, None)
            if btn is None:
                continue
            try:
                dom_node = get_dom(btn)
                def _make_handler(tab_key):
                    def _handler(_evt=None):
                        self._prewarm_single_subform(tab_key)
                    return _handler
                h = _make_handler(key)
                dom_node.addEventListener("pointerenter", h, {"passive": True})
                dom_node.addEventListener("mousedown", h, {"passive": True})
                dom_node.addEventListener("touchstart", h, {"passive": True})
            except Exception:
                pass

    def form_show(self, **event_args):
        if getattr(self, "_prewarm_scheduled", False):
            return
        self._prewarm_scheduled = True
        pending = [k for k in self._ALL_TABS if k not in self._subforms]

        def _step(idx=0):
            if idx >= len(pending):
                return
            self._prewarm_single_subform(pending[idx])
            try:
                anvil.js.window.setTimeout(lambda: _step(idx + 1), 0)
            except Exception:
                pass

        if pending:
            try:
                anvil.js.window.setTimeout(lambda: _step(0), 0)
            except Exception:
                pass

    def _activate_subform(self, key, btn):
        self.highlight_active_button(key)
        btn.background = "#000000"
        if getattr(self, "_active_key", None) == key and len(self.card_2.get_components()) > 0:
            return
        inst = self._get_or_create_subform(key)
        self.card_2.clear()
        if inst is not None:
            self.card_2.add_component(inst, full_width_row=True)
            self._active_key = key

    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "Catalogue":
            self.btn_PriceCatalogue_click()
        elif buttonName == "Location":
            self.btn_Location_click()
        elif buttonName == "Balance":
            self.btn_StockBalance_click()
        elif buttonName == "Analysis":
            self.btn_StocktakeAnalysis_click()
        elif buttonName == "CarParts":
            self.btn_CarPartsUsed_click()

    def highlight_active_button(self, selected_text):
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"
                    comp.foreground = "white"

    def btn_PriceCatalogue_click(self, **event_args):
        """Mount cached/pre-warmed PriceCatalogue in milliseconds."""
        self._activate_subform("PRICE CATALOGUE", self.btn_PriceCatalogue)

    def btn_Location_click(self, **event_args):
        """Mount cached/pre-warmed StockLocation in milliseconds."""
        self._activate_subform("STOCK LOCATION", self.btn_Location)

    def btn_StockBalance_click(self, **event_args):
        """Mount cached/pre-warmed StockBalance in milliseconds."""
        self._activate_subform("STOCK BALANCE", self.btn_StockBalance)

    def btn_StocktakeAnalysis_click(self, **event_args):
        """Mount cached/pre-warmed StocktakeAnalysis in milliseconds."""
        self._activate_subform("STOCK ANALYSIS", self.btn_StocktakeAnalysis)

    def btn_CarPartsUsed_click(self, **event_args):
        """Mount cached/pre-warmed CarPartsUsed in milliseconds."""
        self._activate_subform("CAR PARTS USED", self.btn_CarPartsUsed)

    