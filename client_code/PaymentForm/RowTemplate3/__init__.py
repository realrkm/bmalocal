from ._anvil_designer import RowTemplate3Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class RowTemplate3(RowTemplate3Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        user = anvil.users.get_user()
        self.btn_DeleteRow.visible = bool(user and user.get("role_id") == 1)

    def btn_DeleteRow_click(self, **event_args):
        """This method is called when the button is clicked"""
        payment_id = self.item.get("PaymentID")
        if payment_id is None:
            Notification("This payment cannot be identified.", style="danger").show()
            return

        if not confirm(
            "This will permanently delete the payment record. Continue?",
            title="Delete payment",
        ):
            return

        self.btn_DeleteRow.enabled = False
        try:
            anvil.server.call("delete_payment", payment_id)
        except anvil.server.AppOfflineError:
            Notification("The server is unavailable. The payment was not deleted.", style="danger").show()
        except Exception as exc:
            Notification(f"Could not delete payment: {exc}", style="danger").show()
        else:
            self.parent.items = [
                item
                for item in self.parent.items
                if item.get("PaymentID") != payment_id
            ]
            Notification("Payment deleted.", style="success").show()
        finally:
            self.btn_DeleteRow.enabled = True
