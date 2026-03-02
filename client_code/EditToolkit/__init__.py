from ._anvil_designer import EditToolkitTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class EditToolkit(EditToolkitTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        
        # Set focus to search client
        self.search_keyword_1.text_box_search.focus()

        # Attach the event that fetches technicians
        self.search_keyword_1.set_event_handler("x-get-search-keys", self.getToolkit)
        self.search_keyword_1.text_box_search.placeholder = "Search Toolkit's Name *"

        # Handle what happens when a user selects a result
        self.search_keyword_1.set_event_handler(
            "x-search-hints-result", self.populateClientDetails
        )

        set_default_error_handling(self.handle_server_errors) #Set global server error handler

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            self._show_notification(
                message="Connection to server lost. Please check your internet or try again later.",
                title="Disconnected",
                style="danger"
            )
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            self._show_notification(
                message="Please connect to the internet to proceed.",
                title="No Internet",
                style="warning"
            )
        else:
            self._show_notification(
                message=f"Unexpected error: {exc}",
                title="Error",
                style="danger"
            )

    def _show_notification(self, message, title="", style="danger", timeout=3):
        """
        Displays an Anvil Notification that auto-dismisses after `timeout` seconds.
    
        :param message: The notification body text.
        :param title:   The notification title.
        :param style:   'danger' | 'warning' | 'success' | 'info'
        :param timeout: Seconds before the notification disappears (default: 3).
        """
        notif = Notification(
            message,
            title=title,
            style=style,      # controls the colour — danger=red, warning=orange, success=green, info=blue
            timeout=timeout,  # auto-dismisses after this many seconds
        )
        notif.show()

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def getToolkit(self, **event_args):
        """Return toolkit records to SearchKeyword."""
        results = anvil.server.call("get_toolkits", None)
        return [{"entry": r["ToolkitName"], "ID": r["ID"]} for r in results]

    def populateClientDetails(self, result, **event_args):
        """This method is called when an item is selected"""
        x = anvil.server.call("get_toolkit_details", result["ID"])
        self.txt_name.text = x[0]["ToolkitName"]
        self.txt_amount.text = x[0]["Cost"]

    def btn_Update_click(self, **event_args):
        """This method is called when the 'Save and New' button is clicked"""
        self.btn_Update.enabled = False  # Disable button to prevent multiple clicks

        if self.search_keyword_1.selected_result is None:
            alert("Please select toolkit's name to proceed.", large=False)
            self.search_keyword_1.text_box_search.focus()
            self.btn_Update.enabled =True
            return
        else:
            toolkit_id = self.search_keyword_1.selected_result["ID"]
            
        name = self.txt_name.text.strip().upper()
        amount = self.txt_amount.text

        # Validation
        if not name:
            alert("Please enter toolkit's name.")
            self.txt_name.focus()
            self.btn_Update.enabled = True
            return
        
        elif not amount:
            alert("Please enter toolkit amount.")
            self.txt_amount.focus()
            self.btn_Update.enabled = True
            return

        # Save data
        anvil.server.call("update_toolkit_data", name, amount, toolkit_id)
        alert("Toolkit updated successfully.", title="Success", large=False)

        # Clear form
        self.btn_Close_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)
