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
    assert status_group.count('class="btn-status') == 5
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


def test_instruction_column_always_wraps_on_initial_load():
    styles = (Path(__file__).parents[2] / "theme" / "assets" / "selfservice.css").read_text(
        encoding="utf-8"
    )

    fixed_layout = re.search(
        r"\.kiosk-table:not\(\.service-history-table\)\s*\{([^}]*)\}",
        styles,
    )
    assert fixed_layout
    assert "table-layout: fixed;" in fixed_layout.group(1)

    instruction_col = re.search(
        r"\.kiosk-table th:nth-child\(5\),\s*\.kiosk-table td:nth-child\(5\)\s*\{([^}]*)\}",
        styles,
    )
    assert instruction_col
    assert "white-space: normal;" in instruction_col.group(1)
    assert "overflow-wrap: anywhere;" in instruction_col.group(1)


def test_service_history_table_columns_have_legible_min_widths():
    styles = (Path(__file__).parents[2] / "theme" / "assets" / "selfservice.css").read_text(
        encoding="utf-8"
    )

    table_rule = re.search(r"\.service-history-table\s*\{([^}]*)\}", styles)
    assert table_rule
    assert "min-width: 1550px;" in table_rule.group(1)

    cell_rule = re.search(
        r"\.service-history-table th,\s*\.service-history-table td\s*\{([^}]*)\}",
        styles,
    )
    assert cell_rule
    assert "overflow-wrap: break-word;" in cell_rule.group(1)
    assert "word-break: normal;" in cell_rule.group(1)

    client_instr_rule = re.search(
        r"\.service-history-table th:nth-child\(5\),\s*\.service-history-table td:nth-child\(5\)\s*\{([^}]*)\}",
        styles,
    )
    assert client_instr_rule
    assert "min-width: 240px;" in client_instr_rule.group(1)
