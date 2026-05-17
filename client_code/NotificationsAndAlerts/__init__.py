from ._anvil_designer import NotificationsAndAlertsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..Alerts import Alerts
from ..IncompleteDefectsInfo import IncompleteDefectsInfo
from ..ViewTechnicianPortalDetails import ViewTechnicianPortalDetails
from ..ViewPricingAlertDetails import ViewPricingAlertDetails


class NotificationsAndAlerts(NotificationsAndAlertsTemplate):
    def __init__(self, notificationsandalerts, **properties):
        # Set Form properties and Data Bindings.
        super().__init__(**properties)

        # Any code you write here will run before the form opens.
        data = notificationsandalerts
        notifications = data.get("notifications", [])
        incomplete_defects = data.get("incomplete_defects", [])
        tech_portal_info = data.get("technician_portal", [])
        pricing_alert = data.get("pricing_alert", [])

        if not bool(notifications) and not bool(incomplete_defects) and not bool(tech_portal_info) and not bool(pricing_alert):
            self.label_1.text = "No Information Found"
        else:
            self.label_1.visible=False
            self.btn_alerts.enabled = bool(notifications)
            self.btn_IncompleteDefectsInfo.enabled = bool(incomplete_defects)
            self.btn_ViewTechnicianPortalDetails.enabled = bool(tech_portal_info)
            self.btn_ViewBuyingPriceExceedsSelling.enabled = bool(pricing_alert)

    def btn_alerts_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_alerts.enabled=False
        alert(content=Alerts(), dismissible=False,large=True)
        self.btn_alerts.enabled=True

    def btn_IncompleteDefectsInfo_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_IncompleteDefectsInfo.enabled=False
        alert(content=IncompleteDefectsInfo(), dismissible=False,large=True)
        self.btn_IncompleteDefectsInfo.enabled=True

    def btn_ViewBuyingPriceExceedsSelling_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_ViewBuyingPriceExceedsSelling.enabled=False
        alert(content=ViewPricingAlertDetails(), dismissible=False,large=True)
        self.btn_ViewBuyingPriceExceedsSelling.enabled=True

    def btn_ViewTechnicianPortalDetails_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_ViewTechnicianPortalDetails.enabled=False
        alert(content=ViewTechnicianPortalDetails(), dismissible=False,large=True)
        self.btn_ViewTechnicianPortalDetails.enabled=True