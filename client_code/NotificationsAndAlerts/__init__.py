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

    def __init__(self, user,  **properties):
        self.init_components(**properties)
        self.user = user

        # Load UI
        self.load_notifications()

    def load_notifications(self):
        # Store data for reuse
        self.notificationsandalerts = anvil.server.call_s('fetch_all_dashboard_notifications', self.user)
        
        data = self.notificationsandalerts

        notifications = data.get("notifications", [])
        incomplete_defects = data.get("incomplete_defects", [])
        tech_portal_info = data.get("technician_portal", [])
        pricing_alert = data.get("pricing_alert", [])

        if (
            not notifications
            and not incomplete_defects
            and not tech_portal_info
            and not pricing_alert
        ):
            self.label_1.text = "No Information Found"
            self.label_1.visible = True

        else:
            self.label_1.visible = False

        self.btn_alerts.enabled = bool(notifications)
        self.btn_IncompleteDefectsInfo.enabled = bool(incomplete_defects)
        self.btn_ViewTechnicianPortalDetails.enabled = bool(tech_portal_info)
        self.btn_ViewBuyingPriceExceedsSelling.enabled = bool(pricing_alert)

    def refresh(self, **event_args):

        self.load_notifications()

    def btn_alerts_click(self, **event_args):
        """This method is called when the button is clicked"""
        result = alert(content=Alerts(),dismissible=False,large=True)
        if result:
            self.refresh()
            
    def btn_IncompleteDefectsInfo_click(self, **event_args):
        """This method is called when the button is clicked"""
        result = alert(content=IncompleteDefectsInfo(), dismissible=False,large=True)
        if result:
            self.refresh()
       
    def btn_ViewBuyingPriceExceedsSelling_click(self, **event_args):
        """This method is called when the button is clicked"""
        result = alert(content=ViewPricingAlertDetails(), dismissible=False,large=True)
        if result:
            self.refresh()
        
    def btn_ViewTechnicianPortalDetails_click(self, **event_args):
        """This method is called when the button is clicked"""
        result = alert(content=ViewTechnicianPortalDetails(), dismissible=False,large=True)
        if result:
            self.refresh()
       