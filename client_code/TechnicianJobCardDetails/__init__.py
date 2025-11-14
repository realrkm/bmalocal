from ._anvil_designer import TechnicianJobCardDetailsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..Client import Client
from ..TechniciansDetailsReport import TechniciansDetailsReport
from ..AssignedJobCards import AssignedJobCards
import anvil.js

class TechnicianJobCardDetails(TechnicianJobCardDetailsTemplate):
    def __init__(self, buttonName, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.show_clicked_button(buttonName)

    # This function is called when Contact form loads or when Save And New button is clicked in the forms loaded in card_2 component
    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "Technician":
            self.btn_Technician_click()
        elif buttonName == "AssignedJobCards":
            self.btn_AssignedJobCards_click()

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


    def btn_Technician_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_AssignedJobCards.enabled = False #Prevent clicking before current data content loads
        self.highlight_active_button("TECHNICIANS")
        self.card_2.clear()
        self.card_2.add_component(TechniciansDetailsReport())
        self.card_2.visible = True
        self.btn_Technician.background = "#000000"
        self.btn_AssignedJobCards.enabled = True

    def btn_AssignedJobCards_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Technician.enabled = False #Prevent clicking before current data content loads
        self.highlight_active_button("ASSIGNED JOB CARDS")
        self.card_2.clear()
        self.card_2.add_component(AssignedJobCards())
        self.card_2.visible = True
        self.btn_AssignedJobCards.background = "#000000"
        self.btn_Technician.enabled = True
