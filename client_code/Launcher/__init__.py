from ._anvil_designer import LauncherTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
import json
from anvil.js.window import navigator

_PERMS_STORAGE_KEY = "bma_user_permissions_cache_v1"


def _read_cached_permissions(email, role_id):
    """Read cached permissions from browser sessionStorage if email & role_id match."""
    if not email or role_id is None:
        return None
    try:
        raw = anvil.js.window.sessionStorage.getItem(_PERMS_STORAGE_KEY)
        if not raw:
            return None
        cached = json.loads(raw)
        if cached.get("email") == email and cached.get("role_id") == role_id:
            return cached
    except Exception:
        pass
    return None


def _write_cached_permissions(email, role_id, permissions, is_technician):
    """Persist permissions in browser sessionStorage for instant reload hydration."""
    if not email or role_id is None:
        return
    try:
        payload = json.dumps({
            "email": email,
            "role_id": role_id,
            "permissions": permissions or {},
            "is_technician": bool(is_technician),
        })
        anvil.js.window.sessionStorage.setItem(_PERMS_STORAGE_KEY, payload)
    except Exception:
        pass


class Launcher(LauncherTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        user = anvil.users.get_user()
        email = None
        role_id = None
        try:
            email = user["email"] if user else None
            role_id = user["role_id"] if user else None
        except Exception:
            pass

        # Fast path: hydrate immediately from sessionStorage if available, then
        # let Main silently verify/refresh permissions in the background.
        cached = _read_cached_permissions(email, role_id)
        hydrated_from_cache = False
        context = None
        if cached:
            self.permissions = cached.get("permissions", {})
            is_technician = bool(cached.get("is_technician"))
            hydrated_from_cache = True
        else:
            # Fetch user profile and permissions in a single combined round-trip
            try:
                context = anvil.server.call("get_user_session_context")
            except Exception:
                context = None

            if context:
                self.permissions = context.get("permissions", {})
                user = context.get("user") or user
            else:
                # Fallback: attempt single fetch with defensive role_id extraction
                try:
                    role_id = user.get("role_id") if isinstance(user, dict) else (user["role_id"] if user else None)
                    self.permissions = anvil.server.call("get_user_permissions", role_id) if role_id else {}
                except Exception:
                    self.permissions = {}

            is_technician = (
                (context and context.get("is_technician"))
                or bool(self.permissions.get("TECHNICIAN PORTAL", {}).get("main"))
            )
            _write_cached_permissions(email, role_id, self.permissions, is_technician)

        if is_technician:
            open_form('SelfService')
            user_agent = navigator.userAgent
            # Defer analytics call so it does not block the form transition
            anvil.js.window.setTimeout(lambda: anvil.server.call_s('get_stats', user_agent), 4000)
            return
        else:
            open_form(
                "Main",
                permissions=self.permissions,
                user=user,
                revalidate_permissions=hydrated_from_cache,
            )
        
