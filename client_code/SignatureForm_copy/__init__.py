from ._anvil_designer import SignatureForm_copyTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
import base64


class SignatureForm_copy(SignatureForm_copyTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self.is_drawing = False
        self.last_x = 0
        self.last_y = 0

        # Cache the DOM node and context once
        self._canvas_el = None
        self._ctx = None

        # Mouse events
        self.signature_canvas.set_event_handler("mouse_down", self.mouse_down)
        self.signature_canvas.set_event_handler("mouse_move", self.mouse_move)
        self.signature_canvas.set_event_handler("mouse_up", self.mouse_up)
        self.signature_canvas.set_event_handler("mouse_leave", self.mouse_up)

        # Touch events
        self._setup_touch_events()

    # ── Canvas Setup ─────────────────────────────────────────────

    def _get_canvas_el(self):
        """Get and cache the canvas DOM node"""
        if self._canvas_el is None:
            self._canvas_el = anvil.js.get_dom_node(self.signature_canvas)
        return self._canvas_el

    def _get_ctx(self):
        """Get and cache the 2D drawing context"""
        if self._ctx is None:
            self._ctx = self._get_canvas_el().getContext("2d")
        return self._ctx

    def signature_canvas_reset(self, **event_args):
        """Called when canvas is ready — set drawing styles"""
        ctx = self._get_ctx()
        ctx.strokeStyle = "#000000"
        ctx.lineWidth = 2
        ctx.lineCap = "round"
        ctx.lineJoin = "round"

    def _setup_touch_events(self):
        """Attach native touch events to the canvas DOM node"""
        canvas_el = self._get_canvas_el()

        # Prevent page scroll while signing
        canvas_el.style.touchAction = "none"

        canvas_el.addEventListener("touchstart", self._touch_start, {"passive": False})
        canvas_el.addEventListener("touchmove", self._touch_move, {"passive": False})
        canvas_el.addEventListener("touchend", self._touch_end)
        canvas_el.addEventListener("touchcancel", self._touch_end)

    def _get_touch_coords(self, touch_event):
        """Convert touch screen coords to canvas-relative coords"""
        canvas_el = self._get_canvas_el()
        rect = canvas_el.getBoundingClientRect()
        touch = touch_event.touches[0]
        return (touch.clientX - rect.left, touch.clientY - rect.top)

    # ── Touch Handlers ───────────────────────────────────────────

    def _touch_start(self, event):
        event.preventDefault()
        x, y = self._get_touch_coords(event)
        self.is_drawing = True
        self.last_x = x
        self.last_y = y
        ctx = self._get_ctx()
        ctx.beginPath()
        ctx.moveTo(x, y)

    def _touch_move(self, event):
        event.preventDefault()
        if not self.is_drawing:
            return
        x, y = self._get_touch_coords(event)
        ctx = self._get_ctx()
        ctx.lineTo(x, y)
        ctx.stroke()
        self.last_x = x
        self.last_y = y

    def _touch_end(self, event):
        if self.is_drawing:
            self.is_drawing = False
            ctx = self._get_ctx()
            ctx.closePath()

    # ── Mouse Handlers ───────────────────────────────────────────

    def mouse_down(self, x, y, **event_args):
        self.is_drawing = True
        self.last_x = x
        self.last_y = y
        ctx = self._get_ctx()
        ctx.beginPath()
        ctx.moveTo(x, y)

    def mouse_move(self, x, y, **event_args):
        if not self.is_drawing:
            return
        ctx = self._get_ctx()
        ctx.lineTo(x, y)
        ctx.stroke()
        self.last_x = x
        self.last_y = y

    def mouse_up(self, **event_args):
        if self.is_drawing:
            self.is_drawing = False
            ctx = self._get_ctx()
            ctx.closePath()

    # ── Button Handlers ──────────────────────────────────────────

    def clear_button_click(self, **event_args):
        canvas_el = self._get_canvas_el()
        ctx = self._get_ctx()
        ctx.clearRect(0, 0, canvas_el.width, canvas_el.height)
        self.preview_image.visible = False
        self.message_label.text = "Signature cleared!"
        self.message_label.visible = True
        anvil.js.window.setTimeout(
            lambda: setattr(self.message_label, "visible", False), 3000
        )

    def preview_button_click(self, **event_args):
        if self._is_canvas_blank():
            self.message_label.text = "Please sign before preview."
            self.message_label.visible = True
            return

        data_url = self._get_white_background_data_url()
        self.preview_image.source = data_url
        self.preview_image.visible = True

    # ── Helpers ──────────────────────────────────────────────────

    def _is_canvas_blank(self):
        """Check if canvas has no drawing on it"""
        canvas_el = self._get_canvas_el()
        blank = anvil.js.window.document.createElement("canvas")
        blank.width = canvas_el.width
        blank.height = canvas_el.height
        return canvas_el.toDataURL() == blank.toDataURL()

    def _get_white_background_data_url(self):
        """Export canvas with white background to avoid transparency issues"""
        canvas_el = self._get_canvas_el()
        export_canvas = anvil.js.window.document.createElement("canvas")
        export_canvas.width = canvas_el.width
        export_canvas.height = canvas_el.height
        export_ctx = export_canvas.getContext("2d")
        export_ctx.fillStyle = "#ffffff"
        export_ctx.fillRect(0, 0, export_canvas.width, export_canvas.height)
        export_ctx.drawImage(canvas_el, 0, 0)
        return export_canvas.toDataURL("image/png")

    def get_signature_data(self):
        """Public method — call from other forms to retrieve signature PNG"""
        return self._get_white_background_data_url()

    def save_signature_to_table(self):
        """Optional — saves signature as Anvil media to a Data Table"""
        data_url = self._get_white_background_data_url()
        header, encoded = data_url.split(",", 1)
        binary_data = base64.b64decode(encoded)
        media = anvil.BlobMedia("image/png", binary_data, name="signature.png")
        anvil.server.call("save_signature", media)
