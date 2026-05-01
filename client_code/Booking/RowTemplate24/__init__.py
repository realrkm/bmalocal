from ._anvil_designer import RowTemplate24Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from urllib.parse import quote
import anvil.js.window as window


class RowTemplate24(RowTemplate24Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def btn_SendWhatsAppMessage_click(self, **event_args):
        phone = self.item['Phone']
        customer_name = self.item["Client"]
        vehicle = self.item["RegNo"]
        schedule = self.item["FormattedSchedule"]
    
        # Normalize phone (remove + and non-digits)
        phone = ''.join(filter(str.isdigit, phone))
    
        # Proper message formatting
        message = (
            f"Hi {customer_name},\n\n"
            f"This is a reminder that you have an appointment for vehicle {vehicle} scheduled as follows:\n\n"
            f"Location: BMW CENTER LTD, Along Ngong Road\n"
            f"Date & Time: {schedule}\n\n"
            f"We look forward to seeing you soon."
        )
    
        encoded_message = quote(message)
    
        url = f"https://api.whatsapp.com/send?phone={phone}&text={encoded_message}"
    
        # Open WhatsApp
        window.open(url, "_blank")