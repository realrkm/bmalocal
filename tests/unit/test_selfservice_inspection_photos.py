import base64
import importlib
from pathlib import Path
import subprocess
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


def test_missing_photo_focus_helper_is_available_to_save_handler():
    source_path = Path(__file__).parents[2] / "theme" / "assets" / "selfservice.js"
    source = source_path.read_text(encoding="utf-8")
    start = source.index("    function highlightChecklistMissing(")
    end = source.index("    function renderChecklistCard()", start)
    helpers = source[start:end]
    script = f"""
        const state = {{}};
        const document = {{ getElementById: () => null }};
        {helpers}
        focusMissingInspectionPhoto(['image_1']);
    """

    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_required_inspection_photos_follow_checklist_sections():
    source_path = Path(__file__).parents[2] / "theme" / "assets" / "selfservice.js"
    source = source_path.read_text(encoding="utf-8")
    render_start = source.index("    function renderChecklistCard()")
    render_end = source.index("    // Updates section masters", render_start)
    render_markup = source[render_start:render_end]

    assert render_markup.index("${sectionsHTML}") < render_markup.index(
        "${inspectionPhotoUploadMarkup()}"
    )


def test_saved_selfservice_checklist_excludes_removed_yetu_field():
    source_path = Path(__file__).parents[2] / "theme" / "assets" / "selfservice.js"
    source = source_path.read_text(encoding="utf-8")
    sections_start = source.index("    const CHECKLIST_SECTIONS = [")
    sections_end = source.index("    function checklistStorageKey", sections_start)
    item_id_start = source.index("    function checklistItemId", sections_end)
    item_id_end = source.index("\n    function ", item_id_start + 1)
    payload_start = source.index("    function buildChecklistPayload()", item_id_end)
    payload_end = source.index("    function formatChecklistErrors", payload_start)
    script = f"""
        const state = {{
            activeReg: 'JC-042',
            checklist: {{
                reg: 'JC-042',
                checks: {{ B3: true }},
                fields: {{ 'B3.yetu': 'Yes' }}
            }}
        }};
        function checklistApplies() {{ return true; }}
        function syncChecklistFromDOM() {{}}
        function getChecklist() {{ return state.checklist; }}
        function shortChecklistText(text) {{ return text; }}
        {source[sections_start:sections_end]}
        {source[item_id_start:item_id_end]}
        {source[payload_start:payload_end]}
        const payload = buildChecklistPayload();
        if (payload.list.some(item => item.fields.some(field => field.name === 'yetu'))) {{
            throw new Error('Removed Yetu field was included in the saved checklist.');
        }}
        if (payload.list.some(item => item.item.includes('M-Pesa check'))) {{
            throw new Error('Removed M-Pesa checklist item was included in the saved checklist.');
        }}
    """

    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr


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


def test_inspection_photo_decode_works_without_validate_keyword(monkeypatch):
    module, _ = _load_selfservice_module(monkeypatch)
    standard_decode = base64.b64decode

    def client_decode(encoded):
        return standard_decode(encoded)

    monkeypatch.setattr(module.base64, "b64decode", client_decode)
    images = {
        image_code: _data_url("image/png", b"\x89PNG\r\n\x1a\nphoto")
        for image_code in ("image_1", "image_2", "image_3")
    }

    media = module.SelfService._inspection_photo_media(images)

    assert set(media) == {"image_1", "image_2", "image_3"}
    assert all(photo.get_bytes() == b"\x89PNG\r\n\x1a\nphoto" for photo in media.values())


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
