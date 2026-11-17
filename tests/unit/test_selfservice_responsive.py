import re
from pathlib import Path


def test_service_status_filters_wrap_on_mobile():
    assets = Path(__file__).parents[2] / "theme" / "assets"
    source = (assets / "selfservice.js").read_text(encoding="utf-8")
    styles = (assets / "selfservice.css").read_text(encoding="utf-8")

    assert 'class="service-status-filters"' in source
    status_styles = re.search(
        r"\.service-status-filters\s*\{([^}]*)\}",
        styles,
    )
    assert status_styles
    assert "flex-wrap: wrap;" in status_styles.group(1)
    assert "min-width: 0;" in status_styles.group(1)
