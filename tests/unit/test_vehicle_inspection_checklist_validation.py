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
    anvil = _module("anvil", Notification=notification_factory)
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
        r'<anvil-component type="(CheckBox|TextBox|Image|FileLoader|DatePicker)"'
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
        else:
            component = SimpleNamespace(file=object())
        setattr(form, name, component)
    instance = object.__new__(checklist_class)
    instance.__dict__.update(vars(form))
    instance.jobcardid = 42
    instance.btn_Update = SimpleNamespace(enabled=True)
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
