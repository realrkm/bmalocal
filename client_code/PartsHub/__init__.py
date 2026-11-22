from ._anvil_designer import PartsHubTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class PartsHub(PartsHubTemplate):
    def __init__(self, permissions, **properties):
        """Initialize PartsHub form with permissions and defer loading the first subform."""
        # Set Form properties and Data Bindings
        self.init_components(**properties)
        anvil.js.call("replaceBanner")
        
        # Store permissions
        self.permissions = permissions
        self._initial_subform_loaded = False
        self._first_visible = None

        # Apply permissions to buttons and defer first subform load to form_show
        self.apply_permissions()
        self.set_event_handler("show", self.form_show)

    def form_show(self, **event_args):
        """Load the first authorized subform once the PartsHub container is mounted."""
        if not self._initial_subform_loaded:
            self._initial_subform_loaded = True
            if self._first_visible:
                self.show_clicked_button(self._first_visible)

    def apply_permissions(self):
        """Apply only PARTS HUB-related permissions and record the first available subform."""
        online_perms = self.permissions.get("PARTS HUB", {"main": False, "subs": {}})

        for subsection, value in online_perms["subs"].items():
           if subsection == "Parts Catalog":
                self.btn_PartsCatalog.visible = value
                self.btn_PartsCatalog.enabled = value
                if value and self._first_visible is None:
                    self._first_visible = "Parts Catalog"

           elif subsection == "Order Tracking":
               self.btn_OrderTracking.visible = value
               self.btn_OrderTracking.enabled = value
               if value and self._first_visible is None:
                   self._first_visible = "Order Tracking"

    def show_clicked_button(self, buttonName, **event_args):
        """
        Called when Part Hub form loads in card_2.
        """
        if buttonName == "Parts Catalog":
            self.btn_PartsCatalog_click()
        elif buttonName == "Order Tracking":
            self.btn_OrderTracking_click()
        
    def highlight_active_button(self, selected_text):
        """Highlight the currently active subsection button."""
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"  # Active → black
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"  # Inactive → blue
                    comp.foreground = "white"

    # --- Button click handlers ---
    def btn_PartsCatalog_click(self, **event_args):
        """Load Parts Catalog subform."""
        from ..PartsCatalog import PartsCatalog
        self.highlight_active_button("PARTS CATALOG")
        self.card_2.clear()
        self.card_2.add_component(PartsCatalog(), full_width_row=True)

    def btn_OrderTracking_click(self, **event_args):
        """Load Order Tracking subform."""
        from ..OrderTracking import OrderTracking
        self.highlight_active_button("ORDER TRACKING")
        self.card_2.clear()
        self.card_2.add_component(OrderTracking(), full_width_row=True)

