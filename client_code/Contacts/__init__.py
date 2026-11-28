from ._anvil_designer import ContactsTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModGetData


class Contacts(ContactsTemplate):
    def __init__(self, permissions, **properties):
        """Initialize Contacts form with permissions, cached subforms, and hover/idle pre-warming."""
        self.init_components(**properties)
        anvil.js.call('replaceBanner')

        self.permissions = permissions
        self._initial_subform_loaded = False
        self._first_visible = None
        self._authorized_keys = []
        self._subforms = {}
        self._active_key = None
        self._rt_token = None

        self.apply_permissions()
        self._attach_hover_prewarm()
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

    def _build_subform(self, key):
        if key == "CLIENTS":
            from ..Client import Client
            return Client()
        if key == "TECHNICIANS":
            from ..Tehnicians import Tehnicians
            return Tehnicians()
        if key == "STAFF":
            from ..Staffs import Staffs
            return Staffs()
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

    def _schedule_prewarm_subforms(self):
        keys = [k for k in getattr(self, "_authorized_keys", ()) if k not in self._subforms]

        def _warm_then_step():
            try:
                warm_fn = getattr(ModGetData, "warmContactsCaches", None)
                if callable(warm_fn):
                    warm_fn(self.permissions)
            except Exception:
                pass

            def _step(idx=0):
                if idx >= len(keys):
                    return
                self._prewarm_single_subform(keys[idx])
                try:
                    anvil.js.window.setTimeout(lambda: _step(idx + 1), 0)
                except Exception:
                    pass

            if keys:
                try:
                    anvil.js.window.setTimeout(lambda: _step(0), 0)
                except Exception:
                    pass

        try:
            anvil.js.window.setTimeout(_warm_then_step, 0)
        except Exception:
            pass

    def _attach_hover_prewarm(self):
        get_dom = getattr(anvil.js, "get_dom_node", None)
        if not callable(get_dom):
            return
        button_map = (
            ("btn_Client", "CLIENTS"),
            ("btn_Technician", "TECHNICIANS"),
            ("btn_Staff", "STAFF"),
        )
        for attr, key in button_map:
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

    def _on_contacts_realtime(self, evt=None):
        tech = (getattr(self, "_subforms", None) or {}).get("TECHNICIANS")
        if tech is not None and hasattr(tech, "refresh_toolkits"):
            action = evt.get("action", "") if isinstance(evt, dict) else ""
            if not action or "toolkit" in action:
                tech.refresh_toolkits(force_refresh=True)

    def _unsubscribe_realtime(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt and getattr(self, "_rt_token", None):
                rt.unsubscribe(self._rt_token)
        except Exception:
            pass
        self._rt_token = None

    def form_show(self, **event_args):
        """Mount the first authorized subform and idle-prewarm sibling contact subforms."""
        self._unsubscribe_realtime()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_token = rt.subscribe("contacts", self._on_contacts_realtime)
        except Exception:
            pass

        if not self._initial_subform_loaded:
            self._initial_subform_loaded = True
            if self._first_visible:
                self.show_clicked_button(self._first_visible)
            self._schedule_prewarm_subforms()

    def form_hide(self, **event_args):
        self._unsubscribe_realtime()

    def apply_permissions(self):
        """Apply only CONTACT-related permissions and record authorized subforms."""
        contact_perms = (self.permissions or {}).get("CONTACT", {"main": False, "subs": {}})
        subs = contact_perms.get("subs", {})
        self._authorized_keys = []

        mapping = (
            ("Clients", self.btn_Client, "CLIENTS", "Client"),
            ("Technicians", self.btn_Technician, "TECHNICIANS", "Technician"),
            ("Staff", self.btn_Staff, "STAFF", "Staff"),
        )
        for perm_name, btn, tab_key, first_name in mapping:
            if perm_name in subs:
                allowed = bool(subs[perm_name])
                btn.visible = allowed
                btn.enabled = allowed
                if allowed:
                    self._authorized_keys.append(tab_key)
                    if self._first_visible is None:
                        self._first_visible = first_name

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
        if buttonName == "Client":
            self.btn_Client_click()
        elif buttonName == "Technician":
            self.btn_Technician_click()
        elif buttonName == "Staff":
            self.btn_Staff_click()

    def highlight_active_button(self, selected_text):
        """Highlight the currently active subsection button."""
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"
                    comp.foreground = "white"

    def btn_Client_click(self, **event_args):
        """Mount cached/pre-warmed Clients subform in milliseconds."""
        self._activate_subform("CLIENTS", self.btn_Client)

    def btn_Technician_click(self, **event_args):
        """Mount cached/pre-warmed Technicians subform in milliseconds."""
        self._activate_subform("TECHNICIANS", self.btn_Technician)

    def btn_Staff_click(self, **event_args):
        """Mount cached/pre-warmed Staff subform in milliseconds."""
        self._activate_subform("STAFF", self.btn_Staff)
