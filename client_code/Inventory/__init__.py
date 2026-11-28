from ._anvil_designer import InventoryTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js


class Inventory(InventoryTemplate):
    def __init__(self, permissions, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        self.permissions = permissions
        self._initial_subform_loaded = False
        self._first_visible = None
        self._authorized_keys = []
        self._subforms = {}
        self._active_key = None

        # Apply permissions to buttons and attach hover pre-warming
        self.apply_permissions()
        self._attach_hover_prewarm()

        # Defer loading the subform until after the form is attached
        self.set_event_handler("show", self.form_show)

    def _build_subform(self, key):
        if key == "AddNewParts":
            from ..AddNewParts import AddNewParts
            return AddNewParts()
        if key == "AddMoreStock":
            from ..AddMoreStock import AddMoreStock
            return AddMoreStock()
        if key == "StockTaking":
            from ..StockTake import StockTake
            return StockTake()
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

    def _attach_hover_prewarm(self):
        button_map = (
            ("btn_AddNewParts", "AddNewParts"),
            ("btn_AddMoreStock", "AddMoreStock"),
            ("btn_StockTaking", "StockTaking"),
        )
        for attr, key in button_map:
            btn = getattr(self, attr, None)
            if btn is None:
                continue
            try:
                dom_node = anvil.js.get_dom_node(btn)
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
        """Loads the first authorized subform once the main Inventory container is mounted, then idle-prewarms the rest."""
        if not self._initial_subform_loaded:
            self._initial_subform_loaded = True
            if self._first_visible:
                self.show_clicked_button(self._first_visible)
            self._schedule_prewarm_subforms()

    def apply_permissions(self):
        """Apply only INVENTORY-related permissions and record authorized subforms."""
        inventory_perms = (self.permissions or {}).get("INVENTORY", {"main": False, "subs": {}})
        subs = inventory_perms.get("subs", {})
        self._authorized_keys = []

        mapping = (
            ("Add New Parts", self.btn_AddNewParts, "AddNewParts"),
            ("Add More Stock", self.btn_AddMoreStock, "AddMoreStock"),
            ("Stock Taking", self.btn_StockTaking, "StockTaking"),
        )
        for perm_name, btn, tab_key in mapping:
            if perm_name in subs:
                allowed = bool(subs[perm_name])
                btn.visible = allowed
                btn.enabled = allowed
                if allowed:
                    self._authorized_keys.append(tab_key)
                    if self._first_visible is None:
                        self._first_visible = tab_key

    def _activate_subform(self, key, btn, label_text, full_width=False):
        if getattr(self, "_active_key", None) == key and len(self.card_2.get_components()) > 0:
            self.highlight_active_button(label_text)
            btn.background = "#000000"
            return
        self.highlight_active_button(label_text)
        btn.background = "#000000"
        inst = self._get_or_create_subform(key)
        self.card_2.clear()
        if inst is not None:
            if full_width:
                self.card_2.add_component(inst, full_width_row=True)
            else:
                self.card_2.add_component(inst)
            self._active_key = key

    # This function is called when Inventory form loads or when Save And New button is clicked in the forms loaded in card_2 component
    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "AddNewParts":
            self.btn_AddNewParts_click()
        elif buttonName == "AddMoreStock":
            self.btn_AddMoreStock_click()
        elif buttonName == "StockTaking":
            self.btn_StockTaking_click()

    def highlight_active_button(self, selected_text):
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"
                    comp.foreground = "white"

    def btn_AddNewParts_click(self, **event_args):
        """Mount cached/pre-warmed AddNewParts in milliseconds."""
        self._activate_subform("AddNewParts", self.btn_AddNewParts, "ADD NEW PARTS", full_width=False)

    def btn_AddMoreStock_click(self, **event_args):
        """Mount cached/pre-warmed AddMoreStock in milliseconds."""
        self._activate_subform("AddMoreStock", self.btn_AddMoreStock, "ADD MORE STOCK", full_width=True)

    def btn_StockTaking_click(self, **event_args):
        """Mount cached/pre-warmed StockTake in milliseconds."""
        self._activate_subform("StockTaking", self.btn_StockTaking, "STOCK TAKING", full_width=True)
