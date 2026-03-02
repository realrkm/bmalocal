from ._anvil_designer import ToolkitsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
from ..EditToolkit import EditToolkit



class Toolkits(ToolkitsTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        
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

    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and Close' button is clicked"""
        self.btn_SaveAndNew.enabled = False  # Disable button to prevent multiple clicks

        name = self.txt_name.text.strip().upper()
        amount = self.txt_amount.text

        # Validation
        if not name:
            alert("Please enter toolkit name.")
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return
       
        elif not amount:
            alert("Please enter toolkit amount.")
            self.txt_amount.focus()
            self.btn_SaveAndNew.enabled = True
            return
        
        # Call server function
        duplicate = anvil.server.call("check_duplicate_toolkit", name)
        if duplicate:
            alert(
                "Sorry, a toolkit with that name has already been added. Please enter another toolkit.",
                title="Duplicate Toolkit Found",
                large=False,
            )
            self.txt_amount.text = ""
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return

        # Save data
        anvil.server.call("save_toolkit_data", name, amount)
        alert("Toolkit saved successfully.")

        # Clear form
        self.txt_name.text = ""
        self.txt_amount.text=""
        self.btn_SaveAndNew.enabled = True

    def btn_EditToolkit_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=EditToolkit(), buttons=[], dismissible=False, large=True)

    def btn_Close_click(self, **event_args):
        """This method is called when the form is closed"""
        self.raise_event('x-close-alert', value = True)