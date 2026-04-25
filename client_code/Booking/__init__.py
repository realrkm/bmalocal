from ._anvil_designer import BookingTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class Booking(BookingTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')#Set focus into technician
        self.search_keyword_1.text_box_search.focus()

        # Attach the event that fetches technicians
        self.search_keyword_1.set_event_handler('x-get-search-keys', self.getCustomerName)
        self.search_keyword_1.text_box_search.placeholder = "Search Client's Name *"

    def getCustomerName(self,  **event_args):
        """Return customer records to SearchKeyword."""
        results = anvil.server.call("getTechnicians")
        return [{'entry': r['Fullname'], 'ID': r['ID']} for r in results]