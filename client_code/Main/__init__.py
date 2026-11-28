from ._anvil_designer import MainTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
from .. import ModNavigation
from .. import ModGetData
import anvil.js
import json
from anvil.js import window
from anvil.js.window import navigator, setTimeout
from ..NotificationsAndAlerts import NotificationsAndAlerts

_PERMS_STORAGE_KEY = "bma_user_permissions_cache_v1"


class Main(MainTemplate):

    def __init__(self, permissions=None, user=None, revalidate_permissions=False, **properties):
        self.init_components(**properties)
        self.home_component = self.column_panel_content
        anvil.js.call('replaceBanner')

        self.user = user
        if self.user is None:
            while anvil.users.get_user() is None:
                anvil.users.login_with_form()
            self.user = anvil.users.get_user()

        if self.user:
            if permissions is not None:
                self.permissions = permissions
            else:
                # Standalone fallback: fetch only when permissions was not passed at all
                try:
                    role_id = self.user.get("role_id") if isinstance(self.user, dict) else None
                    self.permissions = anvil.server.call("get_user_permissions", role_id) if role_id else {}
                except Exception:
                    self.permissions = {}
            self.apply_permissions()

            if revalidate_permissions:
                anvil.js.window.setTimeout(self.refresh_permissions_async, 500)

            self.notificationsandalerts = None

            user_agent = navigator.userAgent
            # Defer analytics until after the initial UI rendering and notifications settle
            anvil.js.window.setTimeout(lambda: anvil.server.call_s('get_stats', user_agent), 4000)

            ModNavigation.home_form = self

            set_default_error_handling(
                ModGetData.handle_server_errors
            )

            self.polling_active = True
            self.poll_running = False   # ← guard against stacking
            self.timeout_id = None
            self._rt_tokens = []
            self._rt_conn_token = None
            self._subscribe_realtime()
            # Defer initial notification fetch by 1500ms so dashboard UI paints immediately
            anvil.js.window.setTimeout(self.start_notification_loop, 1500)

            # Trigger an immediate check when user returns to this browser tab
            def _on_visibility_change(*args):
                if not getattr(anvil.js.window.document, "hidden", False) and self.polling_active and not self.poll_running:
                    self.run_notification_poll()

            try:
                anvil.js.window.document.addEventListener("visibilitychange", _on_visibility_change)
            except Exception:
                pass

        # Setup Walkie Talkie Real-Time Chat
        self.live_popup.clear()
        self.live_popup.visible = False
        self.fab_btn.tooltip = "Walkie Talkie Chat"
        self.fab_btn.enabled = True
        self.is_open = False
        self._safe_js_call("setWtChatOpenStatus", False)

        # Build user profile for chat
        user_prof = None
        if self.user:
            try:
                email = self.user.get("email", "") if isinstance(self.user, dict) else (self.user["email"] if "email" in self.user else "")
                role_id = self.user.get("role_id") if isinstance(self.user, dict) else (self.user["role_id"] if "role_id" in self.user else None)
                if email:
                    user_prof = {
                        "email": email,
                        "name": email.split("@")[0],
                        "role_name": "Admin" if role_id == 1 else "Staff",
                    }
                    self._safe_js_call("setWtCurrentUser", user_prof)
            except Exception as e:
                print("Error registering WT current user on login:", e)

        # Defer mounting WalkieTalkieChat slightly so the Main shell & sidebar paint first.
        # Once mounted (hidden), DOM elements (#wtMessagesBody, etc.) are ready for unread badges
        # and instant popup opening.
        self._wt_user_prof = user_prof
        self.walkie_chat = None
        anvil.js.window.setTimeout(self._mount_walkie_chat, 250)
        self._attach_sidebar_prewarm()

        self._safe_js_call("updateWtBadgeDisplay")

    def _attach_sidebar_prewarm(self):
        """Pre-warm Revision & Inventory subforms and lookup caches when hovering sidebar buttons."""
        def _bind_btn(attr_name, handler):
            btn = getattr(self, attr_name, None)
            if btn is None:
                return
            try:
                dom_node = anvil.js.get_dom_node(btn)
                dom_node.addEventListener("pointerenter", handler, {"passive": True})
                dom_node.addEventListener("mousedown", handler, {"passive": True})
                dom_node.addEventListener("touchstart", handler, {"passive": True})
            except Exception:
                pass

        def _warm_revision(_evt=None):
            try:
                with anvil.server.no_loading_indicator:
                    ModGetData.getInterimStaffCached()
                ModNavigation.prewarm_Revision(self.permissions)
            except Exception:
                pass

        def _warm_inventory(_evt=None):
            try:
                with anvil.server.no_loading_indicator:
                    ModGetData.getLocationAndSupplier()
                ModNavigation.prewarm_Inventory(self.permissions)
            except Exception:
                pass

        def _warm_settings(_evt=None):
            try:
                with anvil.server.no_loading_indicator:
                    ModGetData.warmSettingsCaches()
                ModNavigation.prewarm_Settings(self.permissions)
            except Exception:
                pass

        _bind_btn("btn_Revision", _warm_revision)
        _bind_btn("btn_Inventory", _warm_inventory)
        _bind_btn("btn_Settings", _warm_settings)

    def _mount_walkie_chat(self):
        """Lazily mount WalkieTalkieChat after Main finishes initial paint."""
        if self.walkie_chat is not None or not self.user:
            return
        try:
            from ..WalkieTalkieChat import WalkieTalkieChat
            self.walkie_chat = WalkieTalkieChat(user_profile=self._wt_user_prof, on_close=self.close_chat)
            self.live_popup.clear()
            self.live_popup.add_component(self.walkie_chat, full_width_row=True)
            self._safe_js_call("updateWtBadgeDisplay")
        except Exception as e:
            print("Error initializing WalkieTalkieChat:", e)
            self.walkie_chat = None

    def refresh_permissions_async(self):
        """Silently refresh permissions from the server and update sidebar & cache."""
        if not self.user:
            return
        try:
            with anvil.server.no_loading_indicator:
                context = anvil.server.call_s("get_user_session_context")
            if not context:
                return
            fresh_perms = context.get("permissions", {})
            if fresh_perms != self.permissions:
                self.permissions = fresh_perms
                ModNavigation.clear_cached_forms()
                self.apply_permissions()
            try:
                email = self.user.get("email", "") if isinstance(self.user, dict) else self.user["email"]
                role_id = self.user.get("role_id") if isinstance(self.user, dict) else self.user["role_id"]
                anvil.js.window.sessionStorage.setItem(
                    _PERMS_STORAGE_KEY,
                    json.dumps({
                        "email": email,
                        "role_id": role_id,
                        "permissions": fresh_perms,
                        "is_technician": bool(context.get("is_technician")),
                    }),
                )
            except Exception:
                pass
        except Exception as e:
            print(f"Background permission refresh skipped: {e}")

    def _safe_js_call(self, fn_name, *args):
        """Invoke a JS function on window safely without throwing if not yet ready."""
        try:
            fn = getattr(anvil.js.window, fn_name, None)
            if callable(fn):
                fn(*args)
            else:
                anvil.js.call(fn_name, *args)
        except Exception:
            pass

    def close_chat(self):
        """Close the Walkie Talkie chat popup window."""
        self.live_popup.visible = False
        self.is_open = False
        self._safe_js_call("setWtChatOpenStatus", False)

    def _is_ws_connected(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            return bool(rt and rt.isConnected())
        except Exception:
            return False

    def _subscribe_realtime(self):
        """Subscribe Main to live notification and permission invalidation events."""
        self._unsubscribe_realtime()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if not rt:
                return
            self._rt_tokens = [
                rt.subscribe("notifications", lambda evt: self.run_notification_poll()),
                rt.subscribe("permissions", lambda evt: self.refresh_permissions_async()),
            ]
            def _on_conn_change(status):
                if status and status.get("connected"):
                    if self.timeout_id is not None:
                        anvil.js.window.clearTimeout(self.timeout_id)
                        self.timeout_id = None
                    if status.get("reconnected"):
                        self.run_notification_poll()
                elif self.polling_active and self.timeout_id is None:
                    self.timeout_id = anvil.js.window.setTimeout(self.run_notification_poll, 30000)
            self._rt_conn_token = rt.onConnectionChange(_on_conn_change)
        except Exception as e:
            print(f"Main realtime subscription skipped: {e}")

    def _unsubscribe_realtime(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if not rt:
                return
            for tok in getattr(self, "_rt_tokens", []) or []:
                rt.unsubscribe(tok)
            self._rt_tokens = []
            if getattr(self, "_rt_conn_token", None):
                rt.offConnectionChange(self._rt_conn_token)
                self._rt_conn_token = None
        except Exception:
            pass

    def start_notification_loop(self):
        self.polling_active = True
        self.run_notification_poll()

    def run_notification_poll(self, *args):
        """The core polling block — guarded against stacking and inactive tabs."""
        if not self.polling_active or self.poll_running:
            return

        # 1. Skip server query if the browser tab is hidden or minimized
        try:
            if getattr(anvil.js.window.document, "hidden", False):
                if self.polling_active:
                    # Check again in 5s if tab becomes active, without calling the server
                    self.timeout_id = anvil.js.window.setTimeout(self.run_notification_poll, 5000)
                return
        except Exception:
            pass

        self.poll_running = True
        try:
            with anvil.server.no_loading_indicator:
                self.notificationsandalerts = anvil.server.call_s(
                    'fetch_all_dashboard_notifications', self.user
                )
                data = self.notificationsandalerts

                notifications = data.get("notifications", [])
                incomplete_defects = data.get("incomplete_defects", [])
                tech_portal_info = data.get("technician_portal", [])
                pricing_alert = data.get("pricing_alert", [])

                notice = sum([bool(notifications), bool(incomplete_defects), bool(tech_portal_info), bool(pricing_alert)])

                if notice > 0:
                    self.link_1.visible = True
                    self.link_1.text = str(notice)
                    self.link_1.foreground = "#00FF00"
                else:
                    self.link_1.visible = False
                    self.link_1.text = None
                    self.link_1.foreground = "#FFFFFF"

                if notifications:
                    notification = notifications[-1]
                    Notification(
                        f"{notification['jobcard']} - {notification['message']}",
                        style="warning",
                        timeout=3,
                    ).show()

        except Exception as e:
            if "Authentication" in str(e) or "auth" in str(e).lower():
                self.polling_active = False
                self.timeout_id = None
                return
            print(f"Notification poll failed temporarily: {e}")
        finally:
            self.poll_running = False   # ← releases the guard
            if self.polling_active and not self._is_ws_connected():
                # Fallback poll only when WebSocket is offline
                self.timeout_id = anvil.js.window.setTimeout(self.run_notification_poll, 30000)

    def link_1_click(self, **event_args):
        """This method is called when the alert link is clicked"""
        result = alert(content=NotificationsAndAlerts(self.user), title="Notifications And Alerts", dismissible=False, large=False)
        if result:
            # Manually fire one iteration instantly upon dialog close
            self.run_notification_poll()

    # ─────────────────────────────────────────────
    # FAB CLICK: Display / Hide Chat Window
    # ─────────────────────────────────────────────

    def fab_btn_click(self, **event_args):
        if not hasattr(self, "walkie_chat") or self.walkie_chat is None:
            # Lazy initialize WalkieTalkieChat on first user interaction
            from ..WalkieTalkieChat import WalkieTalkieChat
            user_prof = None
            if self.user:
                try:
                    email = self.user.get("email", "") if isinstance(self.user, dict) else (self.user["email"] if "email" in self.user else "")
                    role_id = self.user.get("role_id") if isinstance(self.user, dict) else (self.user["role_id"] if "role_id" in self.user else None)
                    if email:
                        user_prof = {
                            "email": email,
                            "name": email.split("@")[0],
                            "role_name": "Admin" if role_id == 1 else "Staff",
                        }
                except Exception:
                    pass
            self.walkie_chat = WalkieTalkieChat(user_profile=user_prof, on_close=self.close_chat)
            self.live_popup.clear()
            self.live_popup.add_component(self.walkie_chat, full_width_row=True)

        if self.is_open:
            self.close_chat()
        else:
            self.live_popup.visible = True
            self.is_open = True
            self._safe_js_call("setWtChatOpenStatus", True)
            self._safe_js_call("clearWtUnreadCount")
            self._safe_js_call("scrollWtChatToBottom")
            try:
                anvil.js.window.setTimeout(
                    lambda: (
                        self._safe_js_call("scrollWtChatToBottom"),
                        anvil.js.window.document.getElementById("wtInputMessage")
                        and anvil.js.window.document.getElementById("wtInputMessage").focus()
                    ),
                    120,
                )
            except Exception:
                pass

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def apply_permissions(self):
        """Apply user permissions to the sidebar only"""
        section_map = {
            "CONTACT": self.btn_Contact,
            "JOB CARD": self.btn_JobCard,
            "BOOKING": self.btn_Booking,
            "WORKFLOW": self.btn_Workflow,
            "TRACKER": self.btn_Tracker,
            "REVISION": self.btn_Revision,
            "PAYMENT": self.btn_Payment,
            "INVENTORY": self.btn_Inventory,
            "REPORTS": self.btn_Report,
            "PARTS HUB": self.btn_PartsHub,
            "SETTINGS": self.btn_Settings,
            "RESET": self.btn_ResetPassword,
            "FAQs": self.btn_FAQs,
        }

        for section, button in section_map.items():
            section_perms = self.permissions.get(section, {})
            # Hide main button if no access at all
            if not (section_perms.get("main") or any(section_perms.get("subs", {}).values())):
                button.visible = False
                button.enabled = False
            else:
                button.visible = True
                button.enabled = True

    def highlight_active_button(self, selected_text):
        # Loop through all buttons in the panel
        for comp in self.column_panel_navigation.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"  # Highlighted black
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"  # Normal blue
                    comp.foreground = "white"

    def load_component(self, cmpt):
        # Clear only the inner content panel so fab_btn and live_popup are never unmounted
        if hasattr(self, "column_panel_content") and self.column_panel_content in self.column_panel_main.get_components():
            self.column_panel_content.clear()
            self.column_panel_content.add_component(cmpt, full_width_row=True)
        else:
            self.column_panel_main.clear()
            self.column_panel_main.add_component(cmpt, full_width_row=True)
            if self.fab_btn not in self.column_panel_main.get_components():
                self.column_panel_main.add_component(self.fab_btn)
            if self.live_popup not in self.column_panel_main.get_components():
                self.column_panel_main.add_component(self.live_popup)
            self.live_popup.visible = self.is_open

        # Refresh page bindings and keep chat badge in sync
        self.refresh_data_bindings()
        self._safe_js_call("updateWtBadgeDisplay")

    def btn_Contact_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("CONTACT")
        ModNavigation.go_Contact(self.permissions)
        self.call_js('hideSidebarIfModal')

    def btn_JobCard_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("JOB CARD")
        ModNavigation.go_JobCard()
        self.call_js('hideSidebarIfModal')

    def btn_Booking_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("BOOKING")
        ModNavigation.go_Booking()
        self.call_js('hideSidebarIfModal')

    def btn_Workflow_click(self, **event_args):
        self.highlight_active_button("WORKFLOW")
        ModNavigation.go_Workflow(self.permissions)
        self.call_js('hideSidebarIfModal')

    def btn_Tracker_click(self, **event_args):
        self.highlight_active_button("TRACKER")
        ModNavigation.go_Tracker()
        self.call_js('hideSidebarIfModal')

    def btn_Revision_click(self, **event_args):
        self.highlight_active_button("REVISION")
        ModNavigation.go_Revision(self.permissions)
        self.call_js('hideSidebarIfModal')

    def btn_Payment_click(self, **event_args):
        self.highlight_active_button("PAYMENT")
        ModNavigation.go_Payment()
        self.call_js('hideSidebarIfModal')

    def btn_Inventory_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("INVENTORY")
        ModNavigation.go_Inventory(self.permissions)
        self.call_js('hideSidebarIfModal')

    def btn_Report_click(self, **event_args):
        self.highlight_active_button("REPORTS")
        ModNavigation.go_Report(self.permissions)
        self.call_js('hideSidebarIfModal')

    def btn_PartsHub_click(self, **event_args):
        self.highlight_active_button("PARTS HUB")
        ModNavigation.go_PartsHub(self.permissions)
        self.call_js('hideSidebarIfModal')

    def btn_Settings_click(self, **event_args):
        self.highlight_active_button("SETTINGS")
        ModNavigation.go_Settings(self.permissions)
        self.call_js('hideSidebarIfModal')

    def btn_ResetPassword_click(self, **event_args):
        """This method is called when the button is clicked"""
        anvil.users.change_password_with_form()

    def btn_FAQs_click(self, **event_args):
        self.highlight_active_button("FAQs")
        ModNavigation.go_FAQs()
        self.call_js('hideSidebarIfModal')

    def btn_Logout_click(self, **event_args):
        # Stop the poll and realtime listeners first, before anything else
        self.polling_active = False
        self._unsubscribe_realtime()
        if self.timeout_id is not None:
            anvil.js.window.clearTimeout(self.timeout_id)
            self.timeout_id = None
        self.user = None  # Clear user reference immediately
        try:
            ModNavigation.clear_cached_forms()
            from .. import ModCache
            ModCache.clear()
        except Exception:
            pass
        try:
            anvil.js.window.sessionStorage.removeItem(_PERMS_STORAGE_KEY)
        except Exception:
            pass

        # Explicitly disconnect Walkie Talkie chat on logout
        self._safe_js_call("disconnectWtChat")

        self.highlight_active_button("LOGOUT")
        open_form('LogoutBackground')
        anvil.users.logout()
        open_form("Launcher")

    def form_show(self, **events_args):
        """Ensure polling restarts if the form is re-shown"""
        if not self.polling_active:
            self.start_notification_loop()
        self._safe_js_call("updateWtBadgeDisplay")

    def form_hide(self, **events_args):
        self.polling_active = False
        self._unsubscribe_realtime()
        if self.timeout_id is not None:
            anvil.js.window.clearTimeout(self.timeout_id)
            self.timeout_id = None
