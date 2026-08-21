from ._anvil_designer import RowTemplateTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

class RowTemplate(RowTemplateTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self.user = anvil.users.get_user()

    def btn_EditItem_click(self, **event_args):
        """This method is called when the button is clicked"""

        partNo = self.item['PartNo']

        # Call method directly on parent form, going one item up at a time
        self.parent.parent.parent.parent.open_edit_form(partNo)