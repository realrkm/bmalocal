from ._anvil_designer import RevisionTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class Revision(RevisionTemplate):
    def __init__(self, permissions, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        self.permissions = permissions
        self._initial_subform_loaded = False
        self._first_visible = None
        self._authorized_keys = []
        self._subforms = {}
        self._active_key = None

        self._preload_assets()
        # Apply permissions to buttons and defer first subform load to form_show
        self.apply_permissions()
        self._attach_hover_prewarm()
        self.set_event_handler("show", self.form_show)

    def _preload_assets(self):
        try:
            img_cls = getattr(anvil.js.window, "Image", None)
            if img_cls:
                img = img_cls()
                img.src = "_/theme/Invoice Header Logo.jpg"
        except Exception:
            pass

    def _build_subform(self, key):
        if key == "INTERIM QUOTATION":
            from ..InterimQuotation import InterimQuotation
            return InterimQuotation()
        if key == "AMENDED INVOICE":
            from ..AmendedInvoice import AmendedInvoice
            return AmendedInvoice()
        if key == "REPAIR PRIORITIES":
            from ..RepairPriorities import RepairPriorities
            return RepairPriorities()
        if key == "BRAND COMPARISON":
            from ..BrandComparison import BrandComparison
            return BrandComparison()
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
            ("btn_InterimQuotation", "INTERIM QUOTATION"),
            ("btn_AmendedInvoice", "AMENDED INVOICE"),
            ("btn_RepairPriorities", "REPAIR PRIORITIES"),
            ("btn_BrandComparison", "BRAND COMPARISON"),
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
        """Load the first authorized subform once the Revision container is mounted, then idle-prewarm the rest."""
        if not self._initial_subform_loaded:
            self._initial_subform_loaded = True
            if self._first_visible:
                self.show_clicked_button(self._first_visible)
            self._schedule_prewarm_subforms()

    def apply_permissions(self):
        """Apply only REVISION-related permissions and record authorized subforms."""
        revision_perms = (self.permissions or {}).get("REVISION", {"main": False, "subs": {}})
        subs = revision_perms.get("subs", {})
        self._authorized_keys = []

        mapping = (
            ("Interim Quote", self.btn_InterimQuotation, "INTERIM QUOTATION"),
            ("Amended Invoice", self.btn_AmendedInvoice, "AMENDED INVOICE"),
            ("Repair Priorities", self.btn_RepairPriorities, "REPAIR PRIORITIES"),
            ("Brand Comparison", self.btn_BrandComparison, "BRAND COMPARISON"),
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

    def _activate_subform(self, key, btn):
        if getattr(self, "_active_key", None) == key and len(self.card_2.get_components()) > 0:
            self.highlight_active_button(key)
            btn.background = "#000000"
            return
        self.highlight_active_button(key)
        btn.background = "#000000"
        inst = self._get_or_create_subform(key)
        self.card_2.clear()
        if inst is not None:
            self.card_2.add_component(inst)
            self._active_key = key

    # This function is called when Revision form loads or when Save And New button is clicked in the forms loaded in card_2 component
    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "INTERIM QUOTATION":
            self.btn_InterimQuotation_click()
        elif buttonName == "AMENDED INVOICE":
            self.btn_AmendedInvoice_click()
        elif buttonName == "REPAIR PRIORITIES":
            self.btn_RepairPriorities_click()
        elif buttonName == "BRAND COMPARISON":
            self.btn_BrandComparison_click()

    def highlight_active_button(self, selected_text):
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"
                    comp.foreground = "white"
                else:
                    comp.background = "#1976D2"
                    comp.foreground = "white"

    def btn_InterimQuotation_click(self, **event_args):
        """Mount cached/pre-warmed InterimQuotation in milliseconds."""
        self._activate_subform("INTERIM QUOTATION", self.btn_InterimQuotation)

    def btn_AmendedInvoice_click(self, **event_args):
        """Mount cached/pre-warmed AmendedInvoice in milliseconds."""
        self._activate_subform("AMENDED INVOICE", self.btn_AmendedInvoice)

    def btn_RepairPriorities_click(self, **event_args):
        """Mount cached/pre-warmed RepairPriorities in milliseconds."""
        self._activate_subform("REPAIR PRIORITIES", self.btn_RepairPriorities)

    def btn_BrandComparison_click(self, **event_args):
        """Mount cached/pre-warmed BrandComparison in milliseconds."""
        self._activate_subform("BRAND COMPARISON", self.btn_BrandComparison)