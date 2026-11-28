from ._anvil_designer import StaffDetailsReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


class StaffDetailsReport(StaffDetailsReportTemplate):
    def __init__(self, staffID=None, **properties):
        self.init_components(**properties)
        self.staff_id = staffID
        self._rt_token = None
        self._is_mounted = True
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekStaffReportCached", lambda: None)()
        if cached is not None:
            self._apply_cached_rows(cached, staffID)
        else:
            anvil.js.window.setTimeout(self._load_initial_data, 0)

    def _apply_cached_rows(self, rows, staff_id):
        if staff_id is None:
            self.client_repeater.items = rows
        else:
            self.client_repeater.items = [
                {**r, "No": idx}
                for idx, r in enumerate((r for r in rows if r.get("ID") == staff_id), start=1)
            ]

    def set_filter(self, staffID):
        """Filter in-place in 0ms when cache is warm, avoiding full form reconstruction."""
        if self.staff_id == staffID and self.client_repeater.items:
            return
        self.staff_id = staffID
        cached = getattr(ModGetData, "peekStaffReportCached", lambda: None)()
        if cached is not None:
            self._apply_cached_rows(cached, staffID)
            return
        with anvil.server.no_loading_indicator:
            self.refresh_staff_table(staffID)

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        with anvil.server.no_loading_indicator:
            self.refresh_staff_table(self.staff_id)

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
                self._rt_token = rt.subscribe("contacts", self._on_contacts_changed)
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._is_mounted = False
        self._unsubscribe_realtime()

    def _on_contacts_changed(self, evt=None):
        with anvil.server.no_loading_indicator:
            self.refresh_staff_table(self.staff_id, force_refresh=True)

    def refresh_staff_table(self, staffID, force_refresh=False):
        if staffID is None and hasattr(ModGetData, "getStaffReportCached"):
            staffs = ModGetData.getStaffReportCached(force_refresh=force_refresh)
        elif hasattr(ModGetData, "getStaffReportCached"):
            all_staff = ModGetData.getStaffReportCached(force_refresh=force_refresh)
            if all_staff is not None:
                self._apply_cached_rows(all_staff, staffID)
                return
            staffs = anvil.server.call("getStaffReport", staffID)
        else:
            staffs = anvil.server.call("getStaffReport", staffID)
        self.client_repeater.items = staffs
