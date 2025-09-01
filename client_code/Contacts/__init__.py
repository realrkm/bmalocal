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
    def __init__(self, buttonName, permissions,  **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        self.permissions = permissions
        self.apply_permissions()
        self.show_clicked_button(buttonName)
        
    def apply_permissions(self):
        """Apply only CONTACT-related permissions"""
        contact_perms = self.permissions.get("CONTACT", {"main": False, "subs": {}})
        # Example sub buttons (assume they exist in your ContactForm)
        # btn_Client, btn_Technician, btn_Staff
        section_map = {
            "Clients": self.btn_Client,
            "Technicians": self.btn_Technician,
            "Staffs": self.btn_Staff,
        }
      
        # If main CONTACT is False and all subs are False → hide whole form
        if not (contact_perms["main"] or any(contact_perms["subs"].values())):
            self.visible = False
            return

        # Otherwise apply each sub
        for sub_name, button in section_map.items():
            if contact_perms["main"]:
                button.visible = True
                button.enabled = True
            else:
                # Respect subsection permission
                allowed = contact_perms["subs"].get(sub_name, False)
                button.visible = allowed
                button.enabled = allowed
        
    #This function is called when Contact form loads or when Save And New button is clicked in the forms loaded in card_2 component
    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "Client":
            self.btn_Client_click()
        elif buttonName == "Technician":
            self.btn_Technician_click()
        elif buttonName == "Staff":
            self.btn_Staff_click()
            
    def highlight_active_button(self, selected_text):
        # Loop through all buttons in the panel
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"  # Highlighted black
                    comp.foreground = "white"
                else:
                    comp.background = "#0056D6"  # Normal blue
                    comp.foreground = "white"

    def btn_Client_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("CLIENT")
        self.card_2.clear()
        self.card_2.add_component(Client())
        self.btn_Client.background = "#000000"

    def btn_Technician_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("TECHNICIANS")
        self.card_2.clear()
        self.card_2.add_component(Tehnicians())
        self.btn_Technician.background = "#000000"

    def btn_Staff_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("STAFF")
        self.card_2.clear()
        self.card_2.add_component(Staffs())
        self.btn_Staff.background = "#000000"

  