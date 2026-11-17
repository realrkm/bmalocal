import re
from pathlib import Path


def test_service_status_filters_wrap_on_mobile():
    assets = Path(__file__).parents[2] / "theme" / "assets"
    source = (assets / "selfservice.js").read_text(encoding="utf-8")
    styles = (assets / "selfservice.css").read_text(encoding="utf-8")

    status_start = source.index('<button class="btn-status')
    group_start = source.rfind("<div", 0, status_start)
    group_end = source.index("</div>", status_start)
    status_group = source[group_start:group_end]

    assert 'class="service-status-filters"' in status_group
    assert status_group.count('class="btn-status') == 4
    status_styles = re.search(
        r"\.service-status-filters\s*\{([^}]*)\}",
        styles,
    )
    assert status_styles
    assert "flex-wrap: wrap;" in status_styles.group(1)
    assert "min-width: 0;" in status_styles.group(1)

    mobile_status_styles = re.search(
        r"@media \(max-width: 768px\)\s*\{[\s\S]*?\.service-status-filters\s*\{([^}]*)\}",
        styles,
    )
    assert mobile_status_styles
    assert "flex: 1 1 100%;" in mobile_status_styles.group(1)
    assert "width: 100%;" in mobile_status_styles.group(1)
    assert "max-width: 100%;" in mobile_status_styles.group(1)
