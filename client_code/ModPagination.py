"""Reusable Next/Previous pagination bar component for large BMALocal report tables."""
from anvil import FlowPanel, Button, Label


def create_pagination_bar(on_prev, on_next):
    """Build a styled pagination FlowPanel with Previous, Page Info, and Next controls."""
    panel = FlowPanel(align="center", spacing="medium")
    btn_prev = Button(
        text="Previous",
        icon="fa:chevron-left",
        background="#0056D6",
        foreground="white",
        role="raised",
        enabled=False,
    )
    lbl_info = Label(
        text="Page 1 of 1 (0 records)",
        bold=True,
        foreground="#111111",
    )
    btn_next = Button(
        text="Next",
        icon="fa:chevron-right",
        icon_align="right",
        background="#0056D6",
        foreground="white",
        role="raised",
        enabled=False,
    )

    btn_prev.set_event_handler("click", lambda **e: on_prev())
    btn_next.set_event_handler("click", lambda **e: on_next())

    panel.add_component(btn_prev)
    panel.add_component(lbl_info)
    panel.add_component(btn_next)

    return {
        "panel": panel,
        "btn_prev": btn_prev,
        "lbl_info": lbl_info,
        "btn_next": btn_next,
    }


def update_pagination_bar(bar, offset, limit, total):
    """Update page counter label and Previous/Next enabled states."""
    if not bar:
        return
    total = max(0, int(total or 0))
    limit = max(1, int(limit or 50))
    offset = max(0, int(offset or 0))

    total_pages = max(1, (total + limit - 1) // limit)
    current_page = min(total_pages, (offset // limit) + 1)

    bar["lbl_info"].text = f"Page {current_page} of {total_pages} ({total:,} records)"
    bar["btn_prev"].enabled = offset > 0
    bar["btn_next"].enabled = (offset + limit) < total
    bar["panel"].visible = total > limit
