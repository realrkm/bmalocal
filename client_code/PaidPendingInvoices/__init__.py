from ._anvil_designer import PaidPendingInvoicesTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class PaidPendingInvoices(PaidPendingInvoicesTemplate):
    def __init__(self, status, start_date, end_date, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        
        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        self.repeating_panel_1.items = anvil.server.call("getPaidPendingInvoices", status, start_date, end_date)
