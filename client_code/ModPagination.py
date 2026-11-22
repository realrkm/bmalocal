"""Reusable responsive Next/Previous pagination bar for BMALocal report tables."""
from anvil import FlowPanel, Button, Label


def create_pagination_bar(on_prev, on_next):
    """Build a responsive pagination bar with Previous, Page Info, and Next controls."""
    panel = FlowPanel(
        align="center",
        spacing="medium",
        spacing_above="medium",
        spacing_below="medium",
        role="bma-pagination-bar",
    )
    btn_prev = Button(
        text="Previous",
        icon="fa:chevron-left",
        background="#0056D6",
        foreground="white",
        role=["raised", "bma-pagination-btn"],
        enabled=False,
    )
    lbl_info = Label(
        text="Page 1 of 1 (0 records)",
        bold=True,
        foreground="#212121",
        align="center",
        role="bma-pagination-info",
    )
    btn_next = Button(
        text="Next",
        icon="fa:chevron-right",
        icon_align="right",
        background="#0056D6",
        foreground="white",
        role=["raised", "bma-pagination-btn"],
        enabled=False,
    )

    bar = {
        "panel": panel,
        "btn_prev": btn_prev,
        "lbl_info": lbl_info,
        "btn_next": btn_next,
        "_loading": False,
        "_last_state": (0, 50, 0),
    }

    def _handle_prev(**e):
        if bar["_loading"]:
            return
        set_pagination_loading(bar, True)
        try:
            on_prev()
        finally:
            set_pagination_loading(bar, False)

    def _handle_next(**e):
        if bar["_loading"]:
            return
        set_pagination_loading(bar, True)
        try:
            on_next()
        finally:
            set_pagination_loading(bar, False)

    btn_prev.set_event_handler("click", _handle_prev)
    btn_next.set_event_handler("click", _handle_next)

    panel.add_component(btn_prev)
    panel.add_component(lbl_info)
    panel.add_component(btn_next)

    return bar


def set_pagination_loading(bar, is_loading):
    """Disable navigation buttons during in-flight page fetches to prevent double clicks."""
    if not bar:
        return
    bar["_loading"] = bool(is_loading)
    if is_loading:
        bar["btn_prev"].enabled = False
        bar["btn_next"].enabled = False
    else:
        offset, limit, total = bar.get("_last_state", (0, 50, 0))
        update_pagination_bar(bar, offset, limit, total)


def update_pagination_bar(bar, offset, limit, total):
    """Update page counter label and Previous/Next enabled states."""
    if not bar:
        return
    total = max(0, int(total or 0))
    limit = max(1, int(limit or 50))
    offset = max(0, int(offset or 0))
    bar["_last_state"] = (offset, limit, total)

    total_pages = max(1, (total + limit - 1) // limit)
    current_page = min(total_pages, (offset // limit) + 1)

    bar["lbl_info"].text = f"Page {current_page} of {total_pages} ({total:,} records)"
    if not bar.get("_loading"):
        bar["btn_prev"].enabled = offset > 0
        bar["btn_next"].enabled = (offset + limit) < total
    bar["panel"].visible = total > limit
