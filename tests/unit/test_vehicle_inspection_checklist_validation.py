import importlib
import re
import sys
import types
import datetime
from html import unescape
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _load_checklist_module(monkeypatch):
    notification_factory = MagicMock()
    anvil = _module(
        "anvil", Notification=notification_factory, alert=MagicMock()
    )
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module(
        "anvil.server",
        call=MagicMock(return_value={"success": True}),
        AppOfflineError=type("AppOfflineError", (Exception,), {}),
    )
    anvil_users = _module("anvil.users")
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.users = anvil_users

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "client_code.VehicleInspectionChecklist._anvil_designer": _module(
            "client_code.VehicleInspectionChecklist._anvil_designer",
            VehicleInspectionChecklistTemplate=type(
                "VehicleInspectionChecklistTemplate", (), {}
            ),
        ),
    }
    target_module = "client_code.VehicleInspectionChecklist"
    monkeypatch.delitem(sys.modules, target_module, raising=False)
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    module = importlib.import_module(target_module)
    return module, notification_factory


def _make_form(checklist_class):
    template = (
        Path(__file__).parents[2]
        / "client_code"
        / "VehicleInspectionChecklist"
        / "form_template.html"
    ).read_text(encoding="utf-8")
    form = SimpleNamespace()
    pattern = (
        r'<anvil-component type="(CheckBox|TextBox|Image|FileLoader|DatePicker|Label)"'
        r'([^>]*)>'
    )
    for component_type, attributes in re.findall(pattern, template):
        name = re.search(r'name="([^"]+)"', attributes).group(1)
        text_match = re.search(r'prop:text="([^"]*)"', attributes)
        placeholder_match = re.search(r'prop:placeholder="([^"]*)"', attributes)
        label = unescape(
            text_match.group(1)
            if text_match
            else placeholder_match.group(1)
            if placeholder_match
            else ""
        )
        if component_type == "CheckBox":
            component = SimpleNamespace(checked=True, text=label)
        elif component_type == "TextBox":
            enabled = 'prop:enabled="false"' not in attributes
            component = SimpleNamespace(
                enabled=enabled,
                text="completed" if enabled else "",
                placeholder=label,
            )
        elif component_type == "Image":
            component = SimpleNamespace(source=object())
        elif component_type == "DatePicker":
            component = SimpleNamespace(date=datetime.date.today(), placeholder=label)
        elif component_type == "Label":
            component = SimpleNamespace(text=label)
        else:
            component = SimpleNamespace(file=object())
        setattr(form, name, component)
    instance = object.__new__(checklist_class)
    instance.__dict__.update(vars(form))
    instance.jobcardid = 42
    instance.btn_Update = SimpleNamespace(enabled=True)
    instance.raise_event = MagicMock()
    instance._inspection_data_loaded = True
    instance._existing_inspection_images = {
        "image_1": None,
        "image_2": None,
        "image_3": None,
    }
    return instance


@pytest.mark.parametrize(
    ("component_name", "property_name", "blank_value", "expected_category"),
    [
        ("chk_jack", "checked", False, "checkbox"),
        ("text_box_test_drive", "text", "  ", "text"),
        ("image_1", "source", None, "photo"),
        ("image_1", "source", "", "photo"),
        ("date_picker_next_service", "date", None, "date"),
        ("date_picker_time_start", "date", None, "date"),
        ("date_picker_time_end", "date", None, "date"),
    ],
)
def test_update_rejects_blank_checklist_components(
    monkeypatch, component_name, property_name, blank_value, expected_category
):
    checklist_module, notification_factory = _load_checklist_module(monkeypatch)
    form = _make_form(checklist_module.VehicleInspectionChecklist)
    setattr(getattr(form, component_name), property_name, blank_value)
    if expected_category == "photo":
        form.file_loader_1.file = blank_value

    checklist_module.VehicleInspectionChecklist.btn_Update_click(form)

    notification_factory.assert_called_once()
    notification_message = notification_factory.call_args.args[0].lower()
    assert expected_category in notification_message
    notification_factory.return_value.show.assert_called_once()
    checklist_module.anvil.server.call.assert_not_called()


def test_update_accepts_complete_checklist(monkeypatch):
    checklist_module, notification_factory = _load_checklist_module(monkeypatch)

    form = _make_form(checklist_module.VehicleInspectionChecklist)
    checklist_module.VehicleInspectionChecklist.btn_Update_click(form)

    notification_factory.assert_called_once_with(
        "Inspection checklist updated.", style="success"
    )
    notification_factory.return_value.show.assert_called_once()
    checklist_module.anvil.server.call.assert_called_once()
    endpoint, jobcard_id, payload = checklist_module.anvil.server.call.call_args.args
    assert endpoint == "save_update_vehicle_inspection"
    assert jobcard_id == 42
    assert payload["checkboxes"]["chk_jack"] is True
    assert payload["textboxes"]["text_box_test_drive"] == "completed"
    assert payload["dates"]["date_picker_next_service"] == datetime.date.today().isoformat()
    assert payload["images"]["image_1"] is form.file_loader_1.file
    assert form.btn_Update.enabled is True


def test_update_preserves_start_and_end_times(monkeypatch):
    checklist_module, _ = _load_checklist_module(monkeypatch)
    form = _make_form(checklist_module.VehicleInspectionChecklist)
    form.date_picker_time_start.date = datetime.datetime(2026, 11, 9, 9, 15)
    form.date_picker_time_end.date = datetime.datetime(2026, 11, 9, 10, 45)

    checklist_module.VehicleInspectionChecklist.btn_Update_click(form)

    payload = checklist_module.anvil.server.call.call_args.args[2]
    assert payload["dates"]["date_picker_time_start"] == "2026-11-09T09:15:00"
    assert payload["dates"]["date_picker_time_end"] == "2026-11-09T10:45:00"


@pytest.mark.parametrize(
    "handler_name",
    ["date_picker_time_start_change", "date_picker_time_end_change"],
)
def test_time_change_displays_decimal_hours_worked(monkeypatch, handler_name):
    checklist_module, _ = _load_checklist_module(monkeypatch)
    form = _make_form(checklist_module.VehicleInspectionChecklist)
    form.date_picker_time_start.date = datetime.datetime(2026, 11, 9, 9, 15)
    form.date_picker_time_end.date = datetime.datetime(2026, 11, 9, 10, 45)

    getattr(checklist_module.VehicleInspectionChecklist, handler_name)(form)

    assert form.lbl_hrs.text == "Total hrs: 1.50"


def test_time_change_clears_total_when_end_is_before_start(monkeypatch):
    checklist_module, notification_factory = _load_checklist_module(monkeypatch)
    form = _make_form(checklist_module.VehicleInspectionChecklist)
    form.date_picker_time_start.date = datetime.datetime(2026, 11, 9, 10, 0)
    form.date_picker_time_end.date = datetime.datetime(2026, 11, 9, 9, 0)

    checklist_module.VehicleInspectionChecklist.date_picker_time_end_change(form)

    assert form.lbl_hrs.text == "Total hrs: --"
    notification_factory.assert_called_once()
    assert notification_factory.call_args.kwargs["style"] == "warning"


def test_form_loads_saved_vehicle_inspection_on_open(monkeypatch):
    checklist_module, _ = _load_checklist_module(monkeypatch)
    load_data = MagicMock()
    monkeypatch.setattr(
        checklist_module.VehicleInspectionChecklist,
        "_load_existing_inspection_data",
        load_data,
        raising=False,
    )

    form = checklist_module.VehicleInspectionChecklist(42)

    assert form.jobcardid == 42
    load_data.assert_called_once_with()


def test_load_existing_inspection_data_populates_form_and_retains_photos(monkeypatch):
    checklist_module, _ = _load_checklist_module(monkeypatch)
    form = _make_form(checklist_module.VehicleInspectionChecklist)
    form.file_loader_1.file = None
    saved_photo = object()
    saved_data = {
        "checkboxes": {
            "chk_jack": True,
            "chk_safety": False,
            "chk_final": True,
            "chk_torque": True,
            "chk_road_test": True,
            "chk_engine_clean": True,
            "chk_old_parts": True,
            "chk_invoice_explain": True,
        },
        "textboxes": {
            "text_box_voltage": "12.6",
            "txt_next_service_mileage": "125000",
            "txt_efficiency": "95%",
        },
        "dates": {
            "date_picker_next_service": "2027-04-28",
            "date_picker_time_start": "2026-11-09T09:15:00",
            "date_picker_time_end": "2026-11-09T10:45:00",
        },
        "images": {"image_1": saved_photo},
    }
    checklist_module.anvil.server.call.return_value = saved_data

    checklist_module.VehicleInspectionChecklist._load_existing_inspection_data(form)

    checklist_module.anvil.server.call.assert_called_once_with(
        "get_vehicle_inspection_data", 42
    )
    assert form.chk_jack.checked is True
    assert form.chk_safety.checked is False
    assert form.chk_final.checked is True
    assert form.chk_torque.checked is True
    assert form.chk_road_test.checked is True
    assert form.chk_engine_clean.checked is True
    assert form.chk_old_parts.checked is True
    assert form.chk_invoice_explain.checked is True
    assert form.text_box_voltage.text == "12.6"
    assert form.txt_next_service_mileage.text == "125000"
    assert form.txt_efficiency.text == "95%"
    assert form.date_picker_next_service.date == datetime.date(2027, 4, 28)
    assert form.date_picker_time_start.date == datetime.datetime(
        2026, 11, 9, 9, 15
    )
    assert form.date_picker_time_end.date == datetime.datetime(
        2026, 11, 9, 10, 45
    )
    assert form.lbl_hrs.text == "Total hrs: 1.50"
    assert form.image_1.source is saved_photo
    assert form._collect_checklist_data()["images"]["image_1"] is saved_photo
    assert form._inspection_data_loaded is True


def test_load_existing_inspection_data_failure_disables_saving(monkeypatch):
    checklist_module, notification_factory = _load_checklist_module(monkeypatch)
    form = _make_form(checklist_module.VehicleInspectionChecklist)
    checklist_module.anvil.server.call.side_effect = RuntimeError("load failed")

    checklist_module.VehicleInspectionChecklist._load_existing_inspection_data(form)

    assert form._inspection_data_loaded is False
    notification_factory.assert_called_once()
    assert notification_factory.call_args.kwargs["style"] == "danger"
    checklist_module.anvil.server.call.reset_mock()

    checklist_module.VehicleInspectionChecklist.btn_Update_click(form)

    checklist_module.anvil.server.call.assert_not_called()
    assert notification_factory.call_count == 2


def test_update_accepts_numeric_textbox_value(monkeypatch):
    checklist_module, notification_factory = _load_checklist_module(monkeypatch)
    form = _make_form(checklist_module.VehicleInspectionChecklist)
    form.text_box_voltage.text = 12

    checklist_module.VehicleInspectionChecklist.btn_Update_click(form)

    notification_factory.assert_called_once_with(
        "Inspection checklist updated.", style="success"
    )
    payload = checklist_module.anvil.server.call.call_args.args[2]
    assert payload["textboxes"]["text_box_voltage"] == "12"


def test_update_reports_server_offline_and_reenables_button(monkeypatch):
    checklist_module, notification_factory = _load_checklist_module(monkeypatch)
    form = _make_form(checklist_module.VehicleInspectionChecklist)
    checklist_module.anvil.server.call.side_effect = (
        checklist_module.anvil.server.AppOfflineError("offline")
    )

    checklist_module.VehicleInspectionChecklist.btn_Update_click(form)

    assert form.btn_Update.enabled is True
    notification_factory.assert_called_once()
    assert notification_factory.call_args.kwargs["style"] == "danger"
    notification_factory.return_value.show.assert_called_once()


def test_required_field_lists_cover_checklist_template(monkeypatch):
    checklist_module, _ = _load_checklist_module(monkeypatch)
    template = (
        Path(__file__).parents[2]
        / "client_code"
        / "VehicleInspectionChecklist"
        / "form_template.html"
    ).read_text(encoding="utf-8")
    checkboxes = set()
    textboxes = set()
    images = set()
    datepickers = set()
    for component_type, attributes in re.findall(
        r'<anvil-component type="(CheckBox|TextBox|Image|DatePicker)"([^>]*)>',
        template,
    ):
        name = re.search(r'name="([^"]+)"', attributes).group(1)
        if component_type == "CheckBox":
            checkboxes.add(name)
        elif component_type == "TextBox":
            if 'prop:enabled="false"' not in attributes:
                textboxes.add(name)
        elif component_type == "Image":
            images.add(name)
        else:
            datepickers.add(name)

    assert set(checklist_module._REQUIRED_CHECKBOXES) == checkboxes
    assert set(checklist_module._REQUIRED_TEXTBOXES) == textboxes
    assert {name for name, _ in checklist_module._REQUIRED_PHOTOS} == images
    assert set(checklist_module._REQUIRED_DATEPICKERS) == datepickers


@pytest.mark.parametrize(
    ("handler_name", "loader_name", "image_name"),
    [
        ("file_loader_1_change", "file_loader_1", "image_1"),
        ("file_loader_2_change", "file_loader_2", "image_2"),
        ("file_loader_3_change", "file_loader_3", "image_3"),
    ],
)
def test_photo_upload_populates_image_preview(
    monkeypatch, handler_name, loader_name, image_name
):
    checklist_module, _ = _load_checklist_module(monkeypatch)
    form = _make_form(checklist_module.VehicleInspectionChecklist)
    photo = object()
    getattr(form, loader_name).file = photo

    getattr(checklist_module.VehicleInspectionChecklist, handler_name)(form)

    assert getattr(form, image_name).source is photo
