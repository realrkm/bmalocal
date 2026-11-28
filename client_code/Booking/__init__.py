from ._anvil_designer import BookingTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from .. import ModGetData


class Booking(BookingTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        anvil.js.call('replaceBanner')

        self._rt_tokens = []
        self._is_mounted = True
        self._client_regs_cache = {}

        if hasattr(self.repeating_panel_1, "set_event_handler"):
            self.repeating_panel_1.set_event_handler("x-refresh-bookings", self.refresh_data_grid)

        if hasattr(self, "set_event_handler"):
            self.set_event_handler("show", self.form_show)
            self.set_event_handler("hide", self.form_hide)

        cached = getattr(ModGetData, "peekBookingsCached", lambda: None)()
        if cached is not None:
            self.repeating_panel_1.items = cached
        else:
            set_timeout = getattr(getattr(anvil.js, "window", None), "setTimeout", None)
            if callable(set_timeout):
                set_timeout(self._load_initial_data, 0)
            else:
                self.refresh_data_grid()

    def _load_initial_data(self):
        if not self._is_mounted:
            return
        if hasattr(ModGetData, "getBookingsCached"):
            rows = ModGetData.getBookingsCached()
        else:
            rows = anvil.server.call("getBookingDetails")
        if self._is_mounted:
            self.repeating_panel_1.items = rows

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
        self._is_mounted = True
        self._unsubscribe_realtime()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_tokens = [
                    rt.subscribe("bookings", self._on_bookings_changed),
                    rt.subscribe("jobcards", self._on_jobcards_changed),
                ]
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._is_mounted = False
        self._unsubscribe_realtime()

    def _on_jobcards_changed(self, evt=None):
        self._client_regs_cache.clear()

    def _on_bookings_changed(self, evt=None):
        self.refresh_data_grid(force_refresh=True)

    def refresh_data_grid(self, force_refresh=True, **event_args):
        """Reload the upcoming bookings table and update ModCache."""
        if hasattr(ModGetData, "getBookingsCached"):
            self.repeating_panel_1.items = ModGetData.getBookingsCached(force_refresh=force_refresh)
        else:
            self.repeating_panel_1.items = anvil.server.call("getBookingDetails")

    def _speculative_warm_client_regs(self, client_id):
        if client_id is None or client_id in self._client_regs_cache:
            return
        try:
            caller = getattr(anvil.server, "call_s", None) or anvil.server.call
            no_spinner = getattr(anvil.server, "no_loading_indicator", None)
            if no_spinner is not None:
                with no_spinner:
                    regs = caller("getCarRegNoFromClientID", client_id)
            else:
                regs = caller("getCarRegNoFromClientID", client_id)
            self._client_regs_cache[client_id] = regs or []
        except Exception:
            pass

    def btn_SearchCustomer_click(self, **event_args):
        """Search customers (from RAM cache when warm) and speculatively warm result[0] vehicle regs."""
        valueCustomer = self.txt_ClientName.text
        if not valueCustomer or not valueCustomer.strip():
            Notification("Enter Customer's name to proceed", title="Blank Field Found", style="warning", timeout=3).show()
            return

        term = valueCustomer.strip()
        cached_clients = getattr(ModGetData, "peekClientReportCached", lambda: None)()
        if cached_clients is not None:
            low = term.lower()
            result = [
                (r["Fullname"], r["ID"])
                for r in cached_clients
                if low in str(r.get("Fullname") or "").lower() or low in str(r.get("Phone") or "").lower()
            ]
        else:
            result = anvil.server.call("getClientFullnameFromSearchWord", term)

        if result:
            self.drop_down_selectCustomer.items = result
            first_id = result[0][1] if isinstance(result[0], (tuple, list)) and len(result[0]) > 1 else None
            set_timeout = getattr(getattr(anvil.js, "window", None), "setTimeout", None)
            if first_id is not None and callable(set_timeout):
                set_timeout(lambda cid=first_id: self._speculative_warm_client_regs(cid), 0)
        else:
            self.drop_down_selectCustomer.items = []
            Notification("No customers found matching that name.", style="warning").show()

    def drop_down_selectCustomer_change(self, **event_args):
        """Populate vehicle registrations in 0ms when cached, otherwise fetch and cache."""
        selected_id = self.drop_down_selectCustomer.selected_value
        if selected_id:
            if selected_id in self._client_regs_cache:
                self.drop_down_car_reg.items = self._client_regs_cache[selected_id]
            else:
                reg_numbers = anvil.server.call('getCarRegNoFromClientID', selected_id) or []
                self._client_regs_cache[selected_id] = reg_numbers
                self.drop_down_car_reg.items = reg_numbers
        else:
            self.drop_down_car_reg.items = []

    def btn_Save_click(self, **event_args):
        """Validate and save the booking"""
        customer = self.drop_down_selectCustomer.selected_value
        regno = self.drop_down_car_reg.selected_value
        period = self.date_picker_period.date
        details = self.txt_area_details.text

        if not (customer and regno and period and details):
            alert(
                content="Please ensure all fields (Customer, Reg No, Date/Time, and Details) are filled in to proceed.",
                title="Missing Information",
                buttons=[("OK", None)]
            )
        else:
            # Save to DB
            anvil.server.call("saveBookingDetails", customer, regno, period, details)

            # UI Feedback
            Notification("Booking saved successfully!", style="success").show()

            # Refresh the list and clear form
            self.refresh_data_grid()
            self.clear_form()

    def clear_form(self):
        """Reset all input components to their default state"""
        self.txt_ClientName.text = ""
        self.drop_down_selectCustomer.items = []
        self.drop_down_car_reg.items = []
        self.date_picker_period.date = None
        self.txt_area_details.text = ""