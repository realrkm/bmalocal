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
    def __init__(self, buttonName, permissions, **properties):
        self.init_components(**properties)
        self.permissions = permissions

        # Bind button clicks dynamically
        self.btn_Client.set_event_handler("click", lambda **e: self.show_clicked_button("Client"))
        self.btn_Technician.set_event_handler("click", lambda **e: self.show_clicked_button("Technician"))
        self.btn_Staff.set_event_handler("click", lambda **e: self.show_clicked_button("Staff"))

        # Apply permissions and show selected
        self.apply_permissions()
        self.show_clicked_button(buttonName)

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

        for sub_name, button in section_map.items():
            allowed = contact_perms["main"] or contact_perms["subs"].get(sub_name, False)
            button.visible = allowed
            button.enabled = allowed

    def show_clicked_button(self, buttonName, **event_args):
        # Map human labels -> DB subsection keys
        name_to_subsection = {
            "Client": "CLIENTS",
            "Technician": "TECHNICIANS",
            "Staff": "STAFF",
        }

        subsection = name_to_subsection.get(buttonName)
        if not subsection:
            return

        # Button map
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

        perms.safe_load_subform(self, self.permissions, "CONTACT", subsection, button_map, loader_fn_map)

    # loader functions
    def load_client(self):
        self.card_2.clear()
        self.card_2.add_component(Client())

    def load_technicians(self):
        self.card_2.clear()
        self.card_2.add_component(Tehnicians())

    def load_staff(self):
        self.card_2.clear()
        self.card_2.add_component(Staffs())
