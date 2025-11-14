from ._anvil_designer import SearchKeywordTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js 

class SearchKeyword(SearchKeywordTemplate):
    """A search box that produces a list of hints to select from."""

    def __init__(self, **properties):
        # You must call self.init_components() before doing anything else in this function
        self.init_components(**properties)

        # The results panel is initially empty
        anvil.js.call('replaceBanner')
        self.repeating_panel_results.items = []

        # Set up the result handling event
        self.repeating_panel_results.set_event_handler('x-result-selected', self.set_result)

        self.selected_result = None  


    def text_box_search_focus(self, **event_args):
        """Refresh the keys when the search box is selected, and populate the suggestions panel."""
        self.search_keys = self.raise_event('x-get-search-keys')
        self.populate_results(self.text_box_search.text)

    def text_box_search_change(self, **event_args):
        """Populate the suggestions when text is entered."""
        self.populate_results(self.text_box_search.text)

    def text_box_search_pressed_enter(self, **event_args):
        """Choose the top result when enter is pressed."""
        results = self.repeating_panel_results.get_components()
        if results:
            results[0].link_search_result.raise_event('click')

    def populate_results(self, text):
        """Populate the suggestions panel."""
        if text == '':
            self.repeating_panel_results.items = []
        else:
            if not hasattr(self, 'search_keys'):
                self.search_keys = self.raise_event('x-get-search-keys')
    
            self.repeating_panel_results.items = [
                key for key in self.search_keys
                if key['entry'].lower().startswith(text.lower())
            ]

    def set_result(self, result, **event_args):
        """Store the selected result and update the textbox with the entry."""
        self.selected_result = result  # Save full object (e.g., {'entry': 'KME 123A', 'ID': 56})
        self.text_box_search.text = result['entry']  # Show just RegNo in the textbox
        self.repeating_panel_results.items = []
        self.raise_event('x-search-hints-result', result=result)

        