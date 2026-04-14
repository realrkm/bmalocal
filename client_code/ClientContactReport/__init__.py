from ._anvil_designer import ClientContactReportTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class ClientContactReport(ClientContactReportTemplate):
    def __init__(self, clientID, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        self.refresh_client_table(clientID)
        
    def refresh_client_table(self, clientID):
        clients = anvil.server.call('getClientReport', clientID)
        self.client_repeater.items = clients
            
       