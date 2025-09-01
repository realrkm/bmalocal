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
from .. import ModLoadSubformPermissions


class Contacts(ContactsTemplate):
    def __init__(self, permissions, **properties):
        """Initialize Contacts form with permissions and optionally load a subform."""
        # Set Form properties and Data Bindings
        self.init_components(**properties)

        # Store permissions
        self.permissions = permissions

        # Apply permissions to buttons
        self.apply_permissions()

        # Load default or requested subform
        #self.show_clicked_button(buttonName)

    def apply_permissions(self):
        """Apply only CONTACT-related permissions."""
        contact_perms = self.permissions.get("CONTACT", {"main": False, "subs": {}})
        alert(contact_perms)

        # Map subsection names to their corresponding buttons
        section_map = {
            "CLIENTS": self.btn_Client,
            "TECHNICIANS": self.btn_Technician,
            "STAFF": self.btn_Staff,
        }

        # If no permission at all → hide the entire form
        if not (contact_perms["main"] or any(contact_perms["subs"].values())):
            self.visible = False
            return

        # Otherwise, check per subsection
        for sub_name, button in section_map.items():
            if contact_perms["main"]:
                button.visible = True
                button.enabled = True
            else:
                allowed = contact_perms["subs"].get(sub_name, False)
                button.visible = allowed
                button.enabled = allowed

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
        self.highlight_active_button("CLIENT")
        self.card_2.clear()
        self.card_2.add_component(Client())
        self.btn_Client.background = "#000000"

    def btn_Technician_click(self, **event_args):
        """Load Technicians subform."""
        self.highlight_active_button("TECHNICIANS")
        self.card_2.clear()
        self.card_2.add_component(Tehnicians())
        self.btn_Technician.background = "#000000"

    def btn_Staff_click(self, **event_args):
        """Load Staff subform."""
        self.highlight_active_button("STAFF")
        self.card_2.clear()
        self.card_2.add_component(Staffs())
        self.btn_Staff.background = "#000000"
