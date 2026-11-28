from ._anvil_designer import TechnicianJobCardDetailsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class TechnicianJobCardDetails(TechnicianJobCardDetailsTemplate):
    def __init__(self, buttonName="Technician", **properties):
        self.init_components(**properties)
        self._subforms = {}
        self._active_key = None
        self._prewarm_scheduled = False
        self._attach_hover_prewarm()
        self.set_event_handler("show", self.form_show)
        self.show_clicked_button(buttonName)

    def _build_subform(self, key):
        if key == "TECHNICIANS":
            from ..TechniciansDetailsReport import TechniciansDetailsReport
            return TechniciansDetailsReport()
        if key == "ASSIGNED JOB CARDS":
            from ..AssignedJobCards import AssignedJobCards
            return AssignedJobCards()
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
            ("btn_Technician", "TECHNICIANS"),
            ("btn_AssignedJobCards", "ASSIGNED JOB CARDS"),
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
        for key in ("TECHNICIANS", "ASSIGNED JOB CARDS"):
            if key not in self._subforms:
                try:
                    anvil.js.window.setTimeout(lambda k=key: self._prewarm_single_subform(k), 0)
                except Exception:
                    pass

    def _activate_subform(self, key, btn):
        self.highlight_active_button(key)
        btn.background = "#000000"
        self.card_2.visible = True
        if getattr(self, "_active_key", None) == key and len(self.card_2.get_components()) > 0:
            return
        inst = self._get_or_create_subform(key)
        self.card_2.clear()
        if inst is not None:
            self.card_2.add_component(inst, full_width_row=True)
            self._active_key = key

    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "Technician":
            self.btn_Technician_click()
        elif buttonName == "AssignedJobCards":
            self.btn_AssignedJobCards_click()

    def highlight_active_button(self, selected_text):
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"
                    comp.foreground = "white"

    def btn_Technician_click(self, **event_args):
        """Mount cached/pre-warmed TechniciansDetailsReport in milliseconds."""
        self._activate_subform("TECHNICIANS", self.btn_Technician)

    def btn_AssignedJobCards_click(self, **event_args):
        """Mount cached/pre-warmed AssignedJobCards in milliseconds."""
        self._activate_subform("ASSIGNED JOB CARDS", self.btn_AssignedJobCards)
