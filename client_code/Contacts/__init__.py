from ._anvil_designer import ContactsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..Client import Client
from ..Tehnicians import Tehnicians
from ..Staffs import Staffs
import anvil.js

class Contacts(ContactsTemplate):
    def __init__(self, permissions, **properties):
        """Initialize Contacts form with permissions and optionally load a subform."""
        # Set Form properties and Data Bindings
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()

        # Store permissions
        self.permissions = permissions

        # Apply permissions to buttons and load the first available subform
        self.apply_permissions()

    def apply_permissions(self):
        """Apply only CONTACT-related permissions and load the first available subform."""
        contact_perms = self.permissions.get("CONTACT", {"main": False, "subs": {}})

        first_visible = None  # track which subform to load first

        for subsection, value in contact_perms["subs"].items():
            if subsection == "Clients":
                self.btn_Client.visible = value
                self.btn_Client.enabled = value
                if value and first_visible is None:
                    first_visible = "Client"

            elif subsection == "Technicians":
                self.btn_Technician.visible = value
                self.btn_Technician.enabled = value
                if value and first_visible is None:
                    first_visible = "Technician"

            elif subsection == "Staff":
                self.btn_Staff.visible = value
                self.btn_Staff.enabled = value
                if value and first_visible is None:
                    first_visible = "Staff"

        # Load the first visible subform automatically
        if first_visible:
            self.show_clicked_button(first_visible)

    def show_clicked_button(self, buttonName, **event_args):
        """
        Called when Contact form loads or when 'Save And New' button 
        is clicked in the forms loaded in card_2.
        """
        if buttonName == "Client":
            self.btn_Client_click()
        elif buttonName == "Technician":
            self.btn_Technician_click()
        elif buttonName == "Staff":
            self.btn_Staff_click()

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
    def btn_Client_click(self, **event_args):
        """Load Clients subform."""
        self.highlight_active_button("CLIENTS")
        self.card_2.clear()
        self.card_2.add_component(Client())

    def btn_Technician_click(self, **event_args):
        """Load Technicians subform."""
        self.highlight_active_button("TECHNICIANS")
        self.card_2.clear()
        self.card_2.add_component(Tehnicians())

    def btn_Staff_click(self, **event_args):
        """Load Staff subform."""
        self.highlight_active_button("STAFF")
        self.card_2.clear()
        self.card_2.add_component(Staffs())
