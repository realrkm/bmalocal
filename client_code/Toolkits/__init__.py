from ._anvil_designer import ToolkitsTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class Toolkits(ToolkitsTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._mutated = False
        self._prewarmed_edit_toolkit = None
        self._attach_hover_prewarm()

    def _prewarm_edit_modal(self, _evt=None):
        if getattr(self, "_prewarmed_edit_toolkit", None) is not None:
            return
        try:
            from ..EditToolkit import EditToolkit
            self._prewarmed_edit_toolkit = EditToolkit()
        except Exception:
            pass

    def _attach_hover_prewarm(self):
        get_dom = getattr(anvil.js, "get_dom_node", None)
        btn = getattr(self, "btn_EditToolkit", None)
        if not callable(get_dom) or btn is None:
            return
        try:
            dom_node = get_dom(btn)
            dom_node.addEventListener("pointerenter", self._prewarm_edit_modal, {"passive": True})
            dom_node.addEventListener("mousedown", self._prewarm_edit_modal, {"passive": True})
            dom_node.addEventListener("touchstart", self._prewarm_edit_modal, {"passive": True})
        except Exception:
            pass

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def btn_SaveAndNew_click(self, **event_args):
        """This method is called when the 'Save and Close' button is clicked"""
        self.btn_SaveAndNew.enabled = False

        name = self.txt_name.text.strip().upper()
        amount = self.txt_amount.text

        if not name:
            Notification("Please enter toolkit name.", style="warning", timeout=3).show()
            self.txt_name.focus()
            self.btn_SaveAndNew.enabled = True
            return

        elif not amount:
            Notification("Please enter toolkit amount.", style="warning", timeout=3).show()
            self.txt_amount.focus()
            self.btn_SaveAndNew.enabled = True
            return

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

        anvil.server.call("save_toolkit_data", name, amount)
        self._mutated = True
        self._prewarmed_edit_toolkit = None
        Notification("Toolkit saved successfully.", style="warning", timeout=3).show()

        self.txt_name.text = ""
        self.txt_amount.text = ""
        self.btn_SaveAndNew.enabled = True

    def btn_EditToolkit_click(self, **event_args):
        """Open pre-warmed EditToolkit modal in milliseconds."""
        from ..EditToolkit import EditToolkit
        modal = self._prewarmed_edit_toolkit or EditToolkit()
        self._prewarmed_edit_toolkit = None
        res = alert(content=modal, buttons=[], dismissible=False, large=True)
        if res == "updated":
            self._mutated = True
        try:
            anvil.js.window.setTimeout(self._prewarm_edit_modal, 0)
        except Exception:
            pass

    def btn_Close_click(self, **event_args):
        """Close modal and report whether toolkit data mutated."""
        self.raise_event('x-close-alert', value="updated" if self._mutated else False)