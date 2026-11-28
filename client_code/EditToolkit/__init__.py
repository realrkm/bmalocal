from ._anvil_designer import EditToolkitTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModGetData


class EditToolkit(EditToolkitTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._updated = False
        self.search_keyword_1.text_box_search.focus()

        self.search_keyword_1.set_event_handler("x-get-search-keys", self.getToolkit)
        self.search_keyword_1.text_box_search.placeholder = "Search Toolkit's Name *"
        self.search_keyword_1.set_event_handler(
            "x-search-hints-result", self.populateClientDetails
        )

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def getToolkit(self, **event_args):
        """Return cached toolkit records to SearchKeyword in 0ms."""
        if hasattr(ModGetData, "getToolkitsCached"):
            results = ModGetData.getToolkitsCached() or []
        else:
            results = anvil.server.call("get_toolkits", None) or []
        return [{"entry": r["ToolkitName"], "ID": r["ID"]} for r in results]

    def populateClientDetails(self, result, **event_args):
        """Populate toolkit details from RAM cache when Cost is cached, otherwise fetch by ID."""
        toolkit_id = result["ID"]
        cached = getattr(ModGetData, "peekToolkitsCached", lambda: None)()
        match = next((r for r in (cached or ()) if r.get("ID") == toolkit_id and r.get("Cost") is not None), None)
        if match is not None:
            self.txt_name.text = match["ToolkitName"]
            self.txt_amount.text = match["Cost"]
            return
        x = anvil.server.call("get_toolkit_details", toolkit_id)
        self.txt_name.text = x[0]["ToolkitName"]
        self.txt_amount.text = x[0]["Cost"]

    def btn_Update_click(self, **event_args):
        """Update toolkit and notify caller on close."""
        self.btn_Update.enabled = False

        if self.search_keyword_1.selected_result is None:
            Notification("Please select toolkit's name to proceed.", style="warning", timeout=3).show()
            self.search_keyword_1.text_box_search.focus()
            self.btn_Update.enabled = True
            return
        else:
            toolkit_id = self.search_keyword_1.selected_result["ID"]

        name = self.txt_name.text.strip().upper()
        amount = self.txt_amount.text

        if not name:
            Notification("Please enter toolkit's name.", style="warning", timeout=3).show()
            self.txt_name.focus()
            self.btn_Update.enabled = True
            return
        elif not amount:
            Notification("Please enter toolkit amount.", style="warning", timeout=3).show()
            self.txt_amount.focus()
            self.btn_Update.enabled = True
            return

        anvil.server.call("update_toolkit_data", name, amount, toolkit_id)
        self._updated = True
        Notification("Toolkit updated successfully.", title="Success", style="success", timeout=3).show()
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        self.raise_event("x-close-alert", value="updated" if self._updated else False)
