from ._anvil_designer import RowTemplate24Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class RowTemplate24(RowTemplate24Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.

    def btn_SendWhatsAppMessage_click(self, **event_args):
        phone = self.item['Phone']
        customer_name = self.item["Fullname"]
        vehicle = self.item["RegNo"]
        schedule = self.item["FormattedSchedule"]
    
        # Normalize phone (remove + and non-digits)
        phone = ''.join(filter(str.isdigit, phone))
    
        # Build message
        message = (
            f"Hi {customer_name},\n\n"
            f"This is a reminder for your appointment.\n\n"
            f"🚗 Vehicle: {vehicle}\n"
            f"📍 Location: Be Ce LTD, Along Ngo Road\n"
            f"🕒 Date & Time: {schedule}\n\n"
            f"We look forward to seeing you."
        )

        encoded_message = anvil.js.window.encodeURIComponent(message)
    
        url = f"https://wa.me/{phone}?text={encoded_message}"
    
        win = anvil.js.window.open(url, "_blank")

        # Try closing after delay
        anvil.js.window.setTimeout(lambda: win.close(), 3000)