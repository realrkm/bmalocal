import base64
import importlib
import sys
import types
from unittest.mock import MagicMock

import pytest


class FakeMedia:
    def __init__(self, content_type, data, name=None):
        self.content_type = content_type
        self.data = data
        self.name = name

    def get_bytes(self):
        return self.data


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _load_selfservice_module(monkeypatch):
    server = _module(
        "anvil.server",
        call=MagicMock(return_value=True),
        call_s=MagicMock(return_value=42),
    )
    anvil = _module("anvil", BlobMedia=FakeMedia, server=server, users=MagicMock())
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    stubs = {
        "anvil": anvil,
        "anvil.server": server,
        "anvil.users": anvil.users,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.js": _module("anvil.js", call=MagicMock()),
        "client_code.SelfService._anvil_designer": _module(
            "client_code.SelfService._anvil_designer",
            SelfServiceTemplate=type("SelfServiceTemplate", (), {}),
        ),
    }
    target_module = "client_code.SelfService"
    monkeypatch.delitem(sys.modules, target_module, raising=False)
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    return importlib.import_module(target_module), anvil


def _data_url(content_type, content):
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


@pytest.mark.parametrize(
    "images",
    [
        None,
        {},
        {"image_1": _data_url("image/png", b"\x89PNG\r\n\x1a\nimage")},
    ],
)
def test_saving_selfservice_checklist_rejects_missing_photos(monkeypatch, images):
    module, anvil = _load_selfservice_module(monkeypatch)
    form = object.__new__(module.SelfService)

    with pytest.raises(ValueError, match="(?i)all three vehicle inspection photos"):
        form.storeTechDetails(
            "JC-042", "Notes", "Defects", None, "Technician",
            _data_url("image/png", b"signature"),
            checklist=[{"id": "A1"}],
            inspection_images=images,
        )

    anvil.server.call_s.assert_not_called()
    anvil.server.call.assert_not_called()


def test_saving_selfservice_checklist_forwards_photo_media_and_parts(monkeypatch):
    module, anvil = _load_selfservice_module(monkeypatch)
    form = object.__new__(module.SelfService)
    image_bytes = {
        "image_1": b"\x89PNG\r\n\x1a\njackstands",
        "image_2": b"\xff\xd8\xfffault",
        "image_3": b"RIFF1234WEBPdashboard",
    }
    image_types = {
        "image_1": "image/png",
        "image_2": "image/jpeg",
        "image_3": "image/webp",
    }
    images = {
        name: _data_url(image_types[name], content)
        for name, content in image_bytes.items()
    }
    checklist = [{"id": "A1"}]

    form.storeTechDetails(
        "JC-042",
        "Notes",
        "Defects",
        "Oil filter - Qty: 1",
        "Technician",
        _data_url("image/png", b"signature"),
        checklist=checklist,
        inspection_images=images,
    )

    anvil.server.call_s.assert_called_once_with("getJobCardID", "JC-042")
    endpoint, jobcard_id, _, _, parts, _, signature, saved_checklist, saved_images = (
        anvil.server.call.call_args.args
    )
    assert endpoint == "saveOrUpdateTechnicianPortalDefectsAndRequestedParts"
    assert jobcard_id == 42
    assert parts == "Oil filter - Qty: 1"
    assert signature.get_bytes() == b"signature"
    assert saved_checklist == checklist
    assert {
        name: (media.content_type, media.get_bytes())
        for name, media in saved_images.items()
    } == {
        name: (image_types[name], image_bytes[name])
        for name in image_bytes
    }


def test_selfservice_loads_existing_inspection_photo_previews(monkeypatch):
    module, anvil = _load_selfservice_module(monkeypatch)
    form = object.__new__(module.SelfService)
    saved_data = {
        "images": {
            "image_1": FakeMedia("image/png", b"\x89PNG\r\n\x1a\nphoto"),
            "image_2": None,
            "image_3": FakeMedia("image/jpeg", b"\xff\xd8\xffphoto"),
        }
    }
    anvil.server.call.side_effect = [42, saved_data]

    images = form.getVehicleInspectionPhotos("JC-042")

    assert images["image_1"] == _data_url("image/png", b"\x89PNG\r\n\x1a\nphoto")
    assert images["image_2"] is None
    assert images["image_3"] == _data_url("image/jpeg", b"\xff\xd8\xffphoto")
    assert anvil.server.call.call_args_list[0].args == ("getJobCardID", "JC-042")
    assert anvil.server.call.call_args_list[1].args == ("get_vehicle_inspection_data", 42)
