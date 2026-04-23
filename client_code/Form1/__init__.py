from ._anvil_designer import Form1Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.js.window import document

class Form1(Form1Template):
    def __init__(self, **properties):
        self.init_components(**properties)

        # Add a scroll listener to the main content panel
        dom_node = anvil.js.get_dom_node(self.content_panel)
        dom_node.onscroll = self.handle_scroll

    def handle_scroll(self, e):
        # If scrolled down, add a CSS class to change the bar color
        if e.target.scrollTop > 10:
            self.header_panel.role = 'app-bar-elevated'
        else:
            self.header_panel.role = 'large-app-bar'

