from ._anvil_designer import SettingsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js 

class Settings(SettingsTemplate):
    def __init__(self, permissions, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        self.permissions = permissions
        self._initial_subform_loaded = False
        self._first_visible = None
        self._authorized_keys = []
        self._subforms = {}
        self._active_key = None
        self._rt_tokens = []

        # Apply permissions to buttons and attach hover pre-warming
        self.apply_permissions()
        self._attach_hover_prewarm()
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

    def _build_subform(self, key):
        if key == "USER ACCOUNT":
            from ..UserAccounts import UserAccounts
            return UserAccounts()
        if key == "ROLES AND PERMISSIONS":
            from ..UserRolesAndPermissions import UserRolesAndPermissions
            return UserRolesAndPermissions()
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
            ("btn_AddUser", "USER ACCOUNT"),
            ("btn_UserRoles", "ROLES AND PERMISSIONS"),
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

    def _on_users_realtime(self, _evt=None):
        ua = (getattr(self, "_subforms", None) or {}).get("USER ACCOUNT")
        if ua is not None and hasattr(ua, "refresh_users"):
            ua.refresh_users(force_refresh=True)

    def _on_perms_realtime(self, _evt=None):
        rp = (getattr(self, "_subforms", None) or {}).get("ROLES AND PERMISSIONS")
        if rp is not None and hasattr(rp, "refresh_roles"):
            rp.refresh_roles(force_refresh=True)

    def _unsubscribe_realtime(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                for tok in getattr(self, "_rt_tokens", ()):
                    rt.unsubscribe(tok)
        except Exception:
            pass
        self._rt_tokens = []

    def form_show(self, **event_args):
        """Load the first authorized subform once the Settings container is mounted, then idle-prewarm the rest."""
        self._unsubscribe_realtime()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_tokens = [
                    rt.subscribe("users", self._on_users_realtime),
                    rt.subscribe("permissions", self._on_perms_realtime),
                ]
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
        """Apply only SETTINGS-related permissions and record authorized subforms."""
        settings_perms = (self.permissions or {}).get("SETTINGS", {"main": False, "subs": {}})
        subs = settings_perms.get("subs", {})
        self._authorized_keys = []

        mapping = (
            ("User Accounts", self.btn_AddUser, "USER ACCOUNT"),
            ("Roles And Permissions", self.btn_UserRoles, "ROLES AND PERMISSIONS"),
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
        self.card_2.visible = True
        inst = self._get_or_create_subform(key)
        self.card_2.clear()
        if inst is not None:
            self.card_2.add_component(inst, full_width_row=True)
            self._active_key = key

    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "USER ACCOUNT":
            self.btn_AddUser_click()
        elif buttonName == "ROLES AND PERMISSIONS":
            self.btn_UserRoles_click()

    def highlight_active_button(self, selected_text):
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"
                    comp.foreground = "white"

    def btn_AddUser_click(self, **event_args):
        """Mount cached/pre-warmed UserAccounts in milliseconds."""
        self._activate_subform("USER ACCOUNT", self.btn_AddUser)

    def btn_UserRoles_click(self, **event_args):
        """Mount cached/pre-warmed UserRolesAndPermissions in milliseconds."""
        self._activate_subform("ROLES AND PERMISSIONS", self.btn_UserRoles)
       
   