from ._anvil_designer import RevisionTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..InterimQuotation import InterimQuotation
from ..AmendedInvoice import AmendedInvoice
from ..RepairPriorities import RepairPriorities
from ..BrandComparison import BrandComparison
import anvil.js

class Revision(RevisionTemplate):
    def __init__(self, permissions,**properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.permissions = permissions

        # Apply permissions to buttons and load the first available subform
        self.apply_permissions()

    def apply_permissions(self):
        """Apply only REVISION-related permissions and load the first available subform."""
        revision_perms = self.permissions.get("REVISION", {"main": False, "subs": {}})

        first_visible = None  # track which subform to load first

        for subsection, value in revision_perms["subs"].items():
            if subsection == "Interim Quote":
                self.btn_InterimQuotation.visible = value
                self.btn_InterimQuotation.enabled = value
                if value and first_visible is None:
                    first_visible = "INTERIM QUOTATION"

            elif subsection == "Amended Invoice":
                self.btn_AmendedInvoice.visible = value
                self.btn_AmendedInvoice.enabled = value
                if value and first_visible is None:
                    first_visible = "AMENDED INVOICE"

            elif subsection == "Repair Priorities":
                self.btn_RepairPriorities.visible = value
                self.btn_RepairPriorities.enabled = value
                if value and first_visible is None:
                    first_visible = "REPAIR PRIORITIES"

            elif subsection == "Brand Comparison":
                self.btn_BrandComparison.visible = value
                self.btn_BrandComparison.enabled = value
                if value and first_visible is None:
                    first_visible = "BRAND COMPARISON"

        # Load the first visible subform automatically
        if first_visible:
            self.show_clicked_button(first_visible)

    #This function is called when Revision form loads or when Save And New button is clicked in the forms loaded in card_2 component
    def show_clicked_button(self, buttonName, **event_args):
        if buttonName == "INTERIM QUOTATION":
            self.btn_InterimQuotation_click()
        elif buttonName == "AMENDED INVOICE":
            self.btn_AmendedInvoice_click()
        elif buttonName =="REPAIR PRIORITIES":
            self.btn_RepairPriorities_click()
        elif buttonName =="BRAND COMPARISON":
            self.btn_BrandComparison_click()
    

    def highlight_active_button(self, selected_text):
        # Loop through all buttons in the panel
        for comp in self.card_1.get_components():
            if isinstance(comp, Button):
                if comp.text == selected_text:
                    comp.background = "#000000"  # Highlighted black
                    comp.foreground = "white"
                else:
                    comp.background = "#1976D2"  # Normal blue
                    comp.foreground = "white"

    def btn_InterimQuotation_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("INTERIM QUOTATION")
        self.card_2.clear()
        self.card_2.add_component(InterimQuotation())
        self.btn_InterimQuotation.background = "#000000"

    def btn_AmendedInvoice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("AMENDED INVOICE")
        self.card_2.clear()
        self.card_2.add_component(AmendedInvoice())
        self.btn_AmendedInvoice.background = "#000000"

    def btn_RepairPriorities_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("REPAIR PRIORITIES")
        self.card_2.clear()
        self.card_2.add_component(RepairPriorities())
        self.btn_RepairPriorities.background = "#000000"

    def btn_BrandComparison_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.highlight_active_button("BRAND COMPARISON")
        self.card_2.clear()
        self.card_2.add_component(BrandComparison())
        self.btn_BrandComparison.background = "#000000"