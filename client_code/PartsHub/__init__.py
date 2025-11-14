from ._anvil_designer import PartsHubTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..PartsCatalog import PartsCatalog
from ..OrderTracking import OrderTracking
import anvil.js


class PartsHub(PartsHubTemplate):
    def __init__(self, permissions, **properties):
        """Initialize Contacts form with permissions and optionally load a subform."""
        # Set Form properties and Data Bindings
        self.init_components(**properties)
        anvil.js.call("replaceBanner")
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()

        # Store permissions
        self.permissions = permissions

        # Apply permissions to buttons and load the first available subform
        self.apply_permissions()

    def apply_permissions(self):
        """Apply only PARTS HUB-related permissions and load the first available subform."""
        online_perms = self.permissions.get("PARTS HUB", {"main": False, "subs": {}})

        first_visible = None  # track which subform to load first

        for subsection, value in online_perms["subs"].items():
           if subsection == "Parts Catalog":
                self.btn_PartsCatalog.visible = value
                self.btn_PartsCatalog.enabled = value
                if value and first_visible is None:
                    first_visible = "Parts Catalog"

           elif subsection == "Order Tracking":
               self.btn_OrderTracking.visible = value
               self.btn_OrderTracking.enabled = value
               if value and first_visible is None:
                   first_visible = "Order Tracking"
                   
        # Load the first visible subform automatically
        if first_visible:
            self.show_clicked_button(first_visible)

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
        self.highlight_active_button("PARTS CATALOG")
        self.card_2.clear()
        self.card_2.add_component(PartsCatalog())

    def btn_OrderTracking_click(self, **event_args):
        """Load Order Tracking subform."""
        self.highlight_active_button("ORDER TRACKING")
        self.card_2.clear()
        self.card_2.add_component(OrderTracking())

