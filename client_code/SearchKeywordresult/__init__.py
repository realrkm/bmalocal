from ._anvil_designer import SearchKeywordresultTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js

class SearchKeywordresult(SearchKeywordresultTemplate):
    """A single search hint."""

    def __init__(self, **properties):
        # You must call self.init_components() before doing anything else in this function
        self.init_components(**properties)
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()

        self.link_search_result.text = self.item['entry']

    def link_search_result_click(self, **event_args):
        self.parent.raise_event('x-result-selected', result=self.item)
