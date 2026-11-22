from ._anvil_designer import ContactsTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js

class Contacts(ContactsTemplate):
    def __init__(self, permissions, **properties):
        """Initialize Contacts form with permissions and defer loading the first subform."""
        # Set Form properties and Data Bindings
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        
        # Store permissions
        self.permissions = permissions
        self._initial_subform_loaded = False
        self._first_visible = None

        # Apply permissions to buttons and record first available subform
        self.apply_permissions()
        self.set_event_handler("show", self.form_show)

    def form_show(self, **event_args):
        """Load the first authorized subform once the Contacts container is mounted."""
        if not self._initial_subform_loaded:
            self._initial_subform_loaded = True
            if self._first_visible:
                self.show_clicked_button(self._first_visible)

    def apply_permissions(self):
        """Apply only CONTACT-related permissions and record the first available subform."""
        contact_perms = self.permissions.get("CONTACT", {"main": False, "subs": {}})

        for subsection, value in contact_perms["subs"].items():
            if subsection == "Clients":
                self.btn_Client.visible = value
                self.btn_Client.enabled = value
                if value and self._first_visible is None:
                    self._first_visible = "Client"

            elif subsection == "Technicians":
                self.btn_Technician.visible = value
                self.btn_Technician.enabled = value
                if value and self._first_visible is None:
                    self._first_visible = "Technician"

            elif subsection == "Staff":
                self.btn_Staff.visible = value
                self.btn_Staff.enabled = value
                if value and self._first_visible is None:
                    self._first_visible = "Staff"

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
        from ..Client import Client
        self.highlight_active_button("CLIENTS")
        self.card_2.clear()
        self.card_2.add_component(Client(), full_width_row=True)

    def btn_Technician_click(self, **event_args):
        """Load Technicians subform."""
        from ..Tehnicians import Tehnicians
        self.highlight_active_button("TECHNICIANS")
        self.card_2.clear()
        self.card_2.add_component(Tehnicians(), full_width_row=True)

    def btn_Staff_click(self, **event_args):
        """Load Staff subform."""
        from ..Staffs import Staffs
        self.highlight_active_button("STAFF")
        self.card_2.clear()
        self.card_2.add_component(Staffs(), full_width_row=True)
