from ._anvil_designer import StaffDetailsReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class StaffDetailsReport(StaffDetailsReportTemplate):
    def __init__(self, staffID, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        self.staff_id = staffID
        self._rt_token = None
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)
        self.refresh_staff_table(staffID)

    def form_show(self, **event_args):
        self.form_hide()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_token = rt.subscribe("contacts", self._on_contacts_changed)
        except Exception:
            pass

    def form_hide(self, **event_args):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt and self._rt_token:
                rt.unsubscribe(self._rt_token)
        except Exception:
            pass
        self._rt_token = None

    def _on_contacts_changed(self, evt=None):
        with anvil.server.no_loading_indicator:
            self.refresh_staff_table(self.staff_id)

    def refresh_staff_table(self, staffID):
        staffs = anvil.server.call("getStaffReport", staffID)
        self.client_repeater.items = staffs
