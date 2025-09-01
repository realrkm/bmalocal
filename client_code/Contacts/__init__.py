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
from .. import ModLoadSubformPermissions as perms


class Contacts(ContactsTemplate):
    def __init__(self, permissions, **properties):
        self.init_components(**properties)
        self.permissions = permissions
        self.apply_permissions()

    def apply_permissions(self):
        """Apply only CONTACT-related permissions"""
        contact_perms = self.permissions.get("CONTACT", {"main": False, "subs": {}})
        section_map = {
            "CLIENTS": self.btn_Client,
            "TECHNICIANS": self.btn_Technician,
            "STAFF": self.btn_Staff,
        }

        if not (contact_perms["main"] or any(contact_perms["subs"].values())):
            self.visible = False
            return

        # Track if we’ve auto-loaded one subsection
        auto_loaded = False

        for sub_name, button in section_map.items():
            allowed = contact_perms["main"] or contact_perms["subs"].get(sub_name, False)
            button.visible = allowed
            button.enabled = allowed

            # Auto-load the first allowed subsection
            if allowed and not auto_loaded:
                self.show_clicked_button(button.text)
                auto_loaded = True

    def show_clicked_button(self, buttonName, **event_args):
        """Called when a subsection button is clicked OR default-loaded"""
        # Map button labels -> DB subsection keys
        name_to_subsection = {
            "CLIENTS": "CLIENTS",
            "TECHNICIANS": "TECHNICIANS",
            "STAFF": "STAFF",
        }

        subsection = name_to_subsection.get(buttonName)
        
        if not subsection:
            return

        # Button map (for highlighting)
        button_map = {
            "CLIENTS": self.btn_Client,
            "TECHNICIANS": self.btn_Technician,
            "STAFF": self.btn_Staff,
        }

        # Loader functions
        loader_fn_map = {
            "CLIENTS": lambda: self.load_client(),
            "TECHNICIANS": lambda: self.load_technicians(),
            "STAFF": lambda: self.load_staff(),
        }

        # Always goes through centralized permission + highlighting
        perms.safe_load_subform(
            self, self.permissions, "CONTACT", subsection, button_map, loader_fn_map
        )

    # --- Loader functions ---
    def load_client(self):
        self.card_2.clear()
        self.card_2.add_component(Client())

    def load_technicians(self):
        self.card_2.clear()
        self.card_2.add_component(Tehnicians())

    def load_staff(self):
        self.card_2.clear()
        self.card_2.add_component(Staffs())

    # --- Button click handlers (thin wrappers) ---
    def btn_Client_click(self, **event_args):
        self.show_clicked_button("Client")

    def btn_Technician_click(self, **event_args):
        self.show_clicked_button("Technician")

    def btn_Staff_click(self, **event_args):
        self.show_clicked_button("Staff")
