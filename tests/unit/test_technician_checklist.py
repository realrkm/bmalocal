import base64
import datetime
import html
import json
import os
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

try:
    import pytest
except ImportError:
    pytest = None


def _ensure_stub_modules():
    """Ensure Anvil and external runtime dependencies are stubbed when running unit tests offline."""
    if "anvil" not in sys.modules:
        anvil_mod = types.ModuleType("anvil")
        anvil_server = types.ModuleType("anvil.server")
        anvil_server.callable = lambda *a, **kw: (lambda fn: fn)
        anvil_server.background_task = lambda fn: fn
        anvil_server.http_endpoint = lambda *a, **kw: (lambda fn: fn)
        anvil_server.connect = MagicMock()
        anvil_server.wait_forever = MagicMock()
        anvil_users = types.ModuleType("anvil.users")
        anvil_users.get_user = MagicMock(return_value={"email": "admin@bmaauto.com", "role_id": 1})
        anvil_tables = types.ModuleType("anvil.tables")
        anvil_tables.app_tables = MagicMock()
        anvil_media = types.ModuleType("anvil.media")

        anvil_mod.server = anvil_server
        anvil_mod.users = anvil_users
        anvil_mod.tables = anvil_tables
        anvil_mod.media = anvil_media

        sys.modules["anvil"] = anvil_mod
        sys.modules["anvil.server"] = anvil_server
        sys.modules["anvil.users"] = anvil_users
        sys.modules["anvil.tables"] = anvil_tables
        sys.modules["anvil.media"] = anvil_media

    if "mysql" not in sys.modules:
        mysql_mod = types.ModuleType("mysql")
        mysql_conn = types.ModuleType("mysql.connector")
        mysql_pooling = types.ModuleType("mysql.connector.pooling")
        mysql_errors = types.ModuleType("mysql.connector.errors")

        class DummyError(Exception):
            pass

        mysql_conn.Error = DummyError
        mysql_errors.PoolError = DummyError
        mysql_pooling.MySQLConnectionPool = MagicMock()
        mysql_conn.pooling = mysql_pooling
        mysql_conn.errors = mysql_errors
        mysql_mod.connector = mysql_conn

        sys.modules["mysql"] = mysql_mod
        sys.modules["mysql.connector"] = mysql_conn
        sys.modules["mysql.connector.pooling"] = mysql_pooling
        sys.modules["mysql.connector.errors"] = mysql_errors

    for mod_name in ("dotenv", "pdfkit", "openpyxl", "openpyxl.styles", "openpyxl.utils", "bcrypt", "websockets"):
        if mod_name not in sys.modules:
            m = types.ModuleType(mod_name)
            if mod_name == "dotenv":
                m.load_dotenv = MagicMock()
            elif mod_name == "pdfkit":
                m.configuration = MagicMock()
                m.from_string = MagicMock()
            elif mod_name == "openpyxl":
                m.Workbook = MagicMock()
                m.load_workbook = MagicMock()
            elif mod_name == "openpyxl.styles":
                m.Font = MagicMock()
                m.PatternFill = MagicMock()
            elif mod_name == "openpyxl.utils":
                m.get_column_letter = MagicMock()
            sys.modules[mod_name] = m


_ensure_stub_modules()


def _load_callables():
    with patch("anvil.server.connect"), \
         patch("anvil.server.wait_forever"), \
         patch("mysql.connector.pooling.MySQLConnectionPool"), \
         patch("pdfkit.configuration"):
        import server_code.BMALocal as bma
        return bma


def _vehicle_inspection_payload():
    checkboxes = (
        "chk_safety", "chk_jack", "chk_chock", "chk_ppe", "chk_valuables",
        "chk_complain", "chk_test_drive", "chk_scan", "chk_mpesa",
        "chk_service", "chk_oil_level", "chk_oil_filter", "chk_air_filter",
        "chk_coolant", "chk_belt", "chk_battery", "chk_carriage",
        "chk_front_arms", "chk_rear_diff", "chk_shocks", "chk_exhaust",
        "chk_shaft", "chk_oil_leaks", "chk_brakes", "chk_front_pads",
        "chk_rear_pads", "chk_brake_fluid", "chk_tyre_pressure", "chk_final",
        "chk_torque", "chk_road_test", "chk_engine_clean", "chk_old_parts",
        "chk_invoice_explain",
    )
    textboxes = (
        "text_box_test_drive", "text_box_fault_code", "text_box_faults_cleared",
        "text_box_customer_limit", "text_box_cracks", "text_box_voltage",
        "text_box_cca", "text_box_any_play", "text_box_any_issue",
        "text_box_broken", "text_box_rattles", "text_box_vibration",
        "text_box_oil_leaks", "text_box_front_pad_thickness", "text_box_front_disc",
        "text_box_rear_pad_thickness", "text_box_17", "text_box_18",
        "text_box_22", "text_box_tyre_tread", "txt_next_service_mileage",
        "txt_efficiency",
    )

    class ImageMedia:
        content_type = "image/png"

        def get_bytes(self):
            return b"\x89PNG\r\n\x1a\ninspection-image"

    payload = {
        "checkboxes": {name: True for name in checkboxes},
        "textboxes": {name: "completed" for name in textboxes},
        "dates": {
            "date_picker_next_service": "2026-12-01",
            "date_picker_time_start": "2026-11-08T09:15:00",
            "date_picker_time_end": "2026-11-08T10:45:00",
        },
        "images": {
            "image_1": ImageMedia(),
            "image_2": ImageMedia(),
            "image_3": ImageMedia(),
        },
    }
    payload["labels"] = {
        name: name.replace("_", " ")
        for name in (
            tuple(payload["checkboxes"])
            + tuple(payload["textboxes"])
            + tuple(payload["dates"])
        )
    }
    return payload


class TestTechnicianChecklist(unittest.TestCase):
    def test_inspection_pdf_data_includes_jobcard_and_checklist_fields(self):
        bma = _load_callables()
        cursor = MagicMock()
        cursor.fetchone.return_value = (
            42,
            "JC-042",
            "Jane Customer",
            "KDEO042",
            "BMW 320i",
            "N20",
            "WBA123",
            "ENG-42",
            82500,
            datetime.date(2026, 11, 9),
        )
        inspection = {
            "checkboxes": {"chk_jack": True},
            "textboxes": {"text_box_voltage": "12.6"},
            "dates": {"date_picker_time_start": "2026-11-09T09:15:00"},
            "images": {"image_1": object()},
            "labels": {
                "chk_jack": "Jack + 2 Jack Stands placed",
                "text_box_voltage": "Battery voltage",
            },
        }
        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "db_cursor") as mock_db_cursor, \
             patch.object(bma, "get_vehicle_inspection_data", return_value=inspection):
            mock_db_cursor.return_value.__enter__.return_value = cursor
            result = bma.get_inspection_checklist_data_by_job_id(42)

        self.assertEqual(result["jobcard"]["JobCardRef"], "JC-042")
        self.assertEqual(result["jobcard"]["ClientName"], "Jane Customer")
        self.assertEqual(result["checkboxes"], inspection["checkboxes"])
        self.assertEqual(result["textboxes"], inspection["textboxes"])
        self.assertEqual(result["dates"], inspection["dates"])
        self.assertIs(result["images"]["image_1"], inspection["images"]["image_1"])

    def test_fill_inspection_checklist_html_renders_checkboxes_fields_dates_and_images(self):
        bma = _load_callables()
        image_bytes = b"\x89PNG\r\n\x1a\ninspection-photo"

        class InspectionImage:
            content_type = "image/png"

            def get_bytes(self):
                return image_bytes

        saved_data = {
            "jobcard": {
                "JobCardRef": "JC-042",
                "ClientName": "Jane & Co",
                "RegNo": "KDEO042",
                "MakeAndModel": "BMW 320i",
                "EngineCode": "N20",
                "ChassisNo": "WBA123",
                "ReceivedDate": datetime.date(2026, 11, 9),
                "Mileage": 82500,
            },
            "checkboxes": {"chk_jack": True, "chk_chock": False},
            "textboxes": {"text_box_voltage": "<12.6>"},
            "dates": {
                "date_picker_next_service": "2026-12-26",
                "date_picker_time_start": "2026-11-09T09:15:00",
                "date_picker_time_end": "2026-11-09T10:45:00",
            },
            "images": {"image_1": InspectionImage(), "image_2": None, "image_3": None},
            "labels": {
                "chk_jack": "Jack stands",
                "chk_chock": "Wheel chock",
                "text_box_voltage": "Battery voltage",
                "date_picker_next_service": "Next service date",
                "date_picker_time_start": "Time started",
                "date_picker_time_end": "Time finished",
            },
        }
        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "_get_inspection_checklist_data", return_value=saved_data):
            rendered = bma.fillInspectionChecklistData(42, "InspectionChecklist")

        self.assertIn("Jane &amp; Co", rendered)
        self.assertIn("Jack stands", rendered)
        self.assertIn("&#9745;", rendered)
        self.assertIn("&#9744;", rendered)
        self.assertIn("<th>Voltage</th><td>&lt;12.6&gt;</td>", rendered)
        self.assertIn("&lt;12.6&gt;", rendered)
        self.assertIn("2026-12-26", rendered)
        self.assertIn("09:15", rendered)
        self.assertIn("10:45", rendered)
        self.assertIn(
            base64.b64encode(image_bytes).decode("ascii"),
            rendered,
        )
        self.assertIn("Car on jack stands", rendered)

    def test_fill_inspection_checklist_html_omits_duplicate_section_rows_and_checks_saved_items(self):
        bma = _load_callables()
        checkboxes = {name: True for name in bma._VEHICLE_INSPECTION_CHECKBOXES}
        labels = {}
        section_titles = []
        item_labels = []
        for section_code, (header_code, header_name), items, _ in bma._VEHICLE_INSPECTION_SECTIONS:
            title = "Section {} heading".format(section_code)
            labels[header_name] = title
            section_titles.append(title)
            for index, (_item_code, item_name) in enumerate(items, start=1):
                label = "{} item {}".format(section_code, index)
                labels[item_name] = label
                item_labels.append(label)
        saved_data = {
            "jobcard": {},
            "checkboxes": checkboxes,
            "textboxes": {},
            "dates": {},
            "images": {},
            "labels": labels,
        }

        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "_get_inspection_checklist_data", return_value=saved_data):
            rendered = bma.fillInspectionChecklistData(42, "InspectionChecklist")

        for title in section_titles:
            self.assertEqual(rendered.count("<h2>{}</h2>".format(title)), 1)
            self.assertNotIn("<td>{}</td>".format(title), rendered)
        for label in item_labels:
            self.assertIn(
                '<tr><td class="check">&#9745;</td><td>{}</td></tr>'.format(label),
                rendered,
            )
        self.assertEqual(rendered.count('<td class="check">'), len(item_labels))

    def test_fill_inspection_checklist_html_uses_form_placeholders_as_field_labels(self):
        bma = _load_callables()
        template_path = (
            Path(__file__).parents[2]
            / "client_code"
            / "VehicleInspectionChecklist"
            / "form_template.html"
        )
        template = template_path.read_text(encoding="utf-8")
        placeholders = {
            name: html.unescape(placeholder).strip()
            for name, placeholder in re.findall(
                r'<anvil-component type="(?:TextBox|DatePicker)" name="([^"]+)"'
                r'[^>]*?prop:placeholder="([^"]*)"',
                template,
            )
        }
        displayed_names = (
            bma._VEHICLE_INSPECTION_TEXTBOXES + bma._VEHICLE_INSPECTION_DATES
        )
        values = {name: "saved-{}".format(name) for name in bma._VEHICLE_INSPECTION_TEXTBOXES}
        date_values = {name: "2026-11-10" for name in bma._VEHICLE_INSPECTION_DATES}
        saved_data = {
            "jobcard": {},
            "checkboxes": {},
            "textboxes": values,
            "dates": date_values,
            "images": {},
            "labels": {name: "Legacy label" for name in displayed_names},
        }

        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "_get_inspection_checklist_data", return_value=saved_data):
            rendered = bma.fillInspectionChecklistData(42, "InspectionChecklist")

        self.assertTrue(all(name in placeholders for name in displayed_names))
        for name in bma._VEHICLE_INSPECTION_TEXTBOXES:
            expected_row = "<th>{}</th><td>{}</td>".format(
                html.escape(placeholders[name]),
                html.escape(values[name]),
            )
            self.assertIn(expected_row, rendered)
        for name in bma._VEHICLE_INSPECTION_DATES:
            expected_row = "<th>{}</th><td>{}</td>".format(
                html.escape(placeholders[name]),
                html.escape(date_values[name]),
            )
            self.assertIn(expected_row, rendered)

    def test_download_inspection_checklist_returns_pdf_and_removes_temporary_file(self):
        bma = _load_callables()
        temporary_paths = []
        expected_media = object()

        def render_pdf(_html, output_path, **_kwargs):
            temporary_paths.append(output_path)
            with open(output_path, "wb") as pdf_file:
                pdf_file.write(b"%PDF-test")

        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "fillInspectionChecklistData", return_value="<html></html>"), \
             patch.object(bma.pdfkit, "from_string", side_effect=render_pdf), \
             patch.object(
                 bma.anvil.media,
                 "from_file",
                 return_value=expected_media,
                 create=True,
             ) as from_file:
            result = bma.downloadInspectionChecklistPdf(42, "InspectionChecklist")

        self.assertIs(result, expected_media)
        from_file.assert_called_once_with(
            temporary_paths[0],
            "application/pdf",
            name="InspectionChecklist-42.pdf",
        )
        self.assertFalse(os.path.exists(temporary_paths[0]))

    def test_get_vehicle_inspection_data_maps_selfservice_checklist_rows(self):
        bma = _load_callables()
        portal_updated_at = datetime.datetime(2026, 11, 9, 10, 0)
        portal_rows = [
            ("A1", 1, None),
            ("A2", 1, None),
            ("A3", 1, None),
            ("A4", 1, None),
            ("B1", 1, json.dumps([{"name": "noise", "value": "No"}])),
            (
                "B2",
                1,
                json.dumps([
                    {"name": "codes", "value": "P0420"},
                    {"name": "cleared", "value": "After repair"},
                ]),
            ),
            ("B3", 1, json.dumps([{"name": "yetu", "value": "Yes"}])),
            ("C1", 1, None),
            ("C2", 1, None),
            ("C3", 1, None),
            ("C4", 1, None),
            ("C5", 1, json.dumps([{"name": "belts", "value": "No cracks"}])),
            (
                "C6",
                1,
                json.dumps([
                    {"name": "volts", "value": "12.6"},
                    {"name": "cca", "value": "650"},
                ]),
            ),
            ("D1", 1, json.dumps([{"name": "arms", "value": "No play"}])),
            ("D2", 1, json.dumps([{"name": "reardiff", "value": "No play detected"}])),
            ("D3", 1, json.dumps([{"name": "shocks", "value": "No leaks"}])),
            ("D4", 1, json.dumps([{"name": "exhaust", "value": "No rattles"}])),
            ("D5", 1, json.dumps([{"name": "propshaft", "value": "No vibration"}])),
            ("D6", 1, json.dumps([{"name": "leaks", "value": "None"}])),
            (
                "E1",
                1,
                json.dumps([
                    {"name": "fpad", "value": "6"},
                    {"name": "fdisc", "value": "24"},
                ]),
            ),
            (
                "E2",
                1,
                json.dumps([
                    {"name": "rpad", "value": "5"},
                    {"name": "rdisc", "value": "18"},
                ]),
            ),
            ("E3", 1, None),
            (
                "E4",
                1,
                json.dumps([
                    {"name": "pf", "value": "32"},
                    {"name": "pr", "value": "34"},
                    {"name": "tread", "value": "5"},
                ]),
            ),
        ]
        portal_rows.append(
            (
                "V-E1",
                0,
                json.dumps([{"name": "text_box_front_pad_thickness", "value": "2"}]),
                datetime.datetime(2026, 11, 9, 9, 0),
            )
        )
        portal_rows = [
            (*row, portal_updated_at, "Inspection section", "Inspection item")
            if len(row) == 3
            else (*row, "Inspection section", "Inspection item")
            for row in portal_rows
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [portal_rows, []]

        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            mock_db_cursor.return_value.__enter__.return_value = mock_cursor
            result = bma.get_vehicle_inspection_data(42)

        self.assertTrue(result["checkboxes"]["chk_safety"])
        self.assertTrue(result["checkboxes"]["chk_jack"])
        self.assertTrue(result["checkboxes"]["chk_complain"])
        self.assertTrue(result["checkboxes"]["chk_test_drive"])
        self.assertTrue(result["checkboxes"]["chk_service"])
        self.assertTrue(result["checkboxes"]["chk_carriage"])
        self.assertTrue(result["checkboxes"]["chk_brakes"])
        self.assertEqual(result["textboxes"]["text_box_test_drive"], "No")
        self.assertEqual(result["textboxes"]["text_box_fault_code"], "P0420")
        self.assertEqual(result["textboxes"]["text_box_faults_cleared"], "After repair")
        self.assertEqual(result["textboxes"]["text_box_customer_limit"], "Yes")
        self.assertEqual(result["textboxes"]["text_box_cracks"], "No cracks")
        self.assertEqual(result["textboxes"]["text_box_voltage"], "12.6")
        self.assertEqual(result["textboxes"]["text_box_cca"], "650")
        self.assertEqual(result["textboxes"]["text_box_any_play"], "No play")
        self.assertEqual(
            result["textboxes"]["text_box_any_issue"], "No play detected"
        )
        self.assertEqual(result["textboxes"]["text_box_front_pad_thickness"], "6")
        self.assertEqual(result["textboxes"]["text_box_front_disc"], "24")
        self.assertEqual(result["textboxes"]["text_box_rear_pad_thickness"], "5")
        self.assertEqual(result["textboxes"]["text_box_17"], "18")
        self.assertEqual(result["textboxes"]["text_box_18"], "32")
        self.assertEqual(result["textboxes"]["text_box_22"], "34")
        self.assertEqual(result["textboxes"]["text_box_tyre_tread"], "5")

    def test_get_vehicle_inspection_data_prefers_newer_legacy_rows(self):
        bma = _load_callables()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [
                (
                    "A1",
                    1,
                    json.dumps([{"name": "noise", "value": "Portal value"}]),
                    datetime.datetime(2026, 11, 9, 9, 0),
                    "Portal section",
                    "Portal item",
                ),
                (
                    "V-B2",
                    1,
                    json.dumps([{"name": "text_box_test_drive", "value": "Legacy value"}]),
                    datetime.datetime(2026, 11, 9, 10, 0),
                    "Legacy section",
                    "Legacy item",
                ),
            ],
            [],
        ]

        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            mock_db_cursor.return_value.__enter__.return_value = mock_cursor
            result = bma.get_vehicle_inspection_data(42)

        self.assertTrue(result["checkboxes"]["chk_test_drive"])
        self.assertEqual(result["textboxes"]["text_box_test_drive"], "Legacy value")

    def test_technician_portal_checklist_requires_all_inspection_photos(self):
        bma = _load_callables()
        checklist = [
            {
                "id": "A1",
                "section": "A",
                "section_title": "A. SAFETY BEFORE LIFT - MANDATORY",
                "item": "Jack + 2 Jack Stands placed",
                "checked": True,
                "fields": [],
            }
        ]
        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            with self.assertRaisesRegex(ValueError, "(?i)all three inspection photos"):
                bma.saveOrUpdateTechnicianPortalDefectsAndRequestedParts(
                    jobcardID=42,
                    tech_notes="Engine check done",
                    defects="No defects",
                    requiredparts="None",
                    staff="John Tech",
                    signature=None,
                    checklist=checklist,
                )

        mock_db_cursor.assert_not_called()

    def test_technician_portal_checklist_rejects_unsupported_photo_before_saving(self):
        bma = _load_callables()
        checklist = [{"id": "A1", "section": "A", "section_title": "Safety", "item": "Stands"}]
        images = _vehicle_inspection_payload()["images"]

        class UnsupportedImage:
            content_type = "image/gif"

            @staticmethod
            def get_bytes():
                return b"GIF89a"

        images["image_1"] = UnsupportedImage()
        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            with self.assertRaisesRegex(ValueError, "Unsupported inspection photo format"):
                bma.saveOrUpdateTechnicianPortalDefectsAndRequestedParts(
                    jobcardID=42,
                    tech_notes="Engine check done",
                    defects="No defects",
                    requiredparts="None",
                    staff="John Tech",
                    signature=None,
                    checklist=checklist,
                    inspection_images=images,
                )

        mock_db_cursor.assert_not_called()

    def test_save_or_update_tech_portal_with_checklist_happy_path(self):
        bma = _load_callables()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Simulate new record insert

        mock_sig = MagicMock()
        mock_sig.get_bytes.return_value = b"png-bytes"

        checklist = [
            {
                "id": "A1",
                "section": "A",
                "section_title": "A. SAFETY BEFORE LIFT - MANDATORY",
                "item": "Jack + 2 Jack Stands placed - Photo taken to WhatsApp Group",
                "checked": True,
                "fields": [],
            },
            {
                "id": "E1",
                "section": "E",
                "section_title": "E. BRAKES & SUSPENSION (CRITICAL)",
                "item": "Front pads thickness mm (min 3mm) - Discs mm - Sensors replaced",
                "checked": True,
                "fields": [
                    {"name": "fpad", "label": "Front pads thickness (mm)", "value": "6.5"},
                    {"name": "fdisc", "label": "Front discs (mm)", "value": "22.0"},
                ],
            },
        ]

        with tempfile.TemporaryDirectory() as image_dir, \
             patch.object(bma, "VEHICLE_INSPECTION_IMAGE_DIR", image_dir), \
             patch("anvil.users.get_user", return_value={"email": "admin@bmaauto.com", "role_id": 1}), \
             patch.object(bma, "db_cursor") as mock_db_cursor, \
             patch.object(bma, "publish_technician_portal_notification", create=True):
            mock_db_cursor.return_value.__enter__.return_value = mock_cursor

            res = bma.saveOrUpdateTechnicianPortalDefectsAndRequestedParts(
                jobcardID=42,
                tech_notes="Engine check done",
                defects="Worn front brake pads",
                requiredparts="Front Brake Pads - Qty: 1",
                staff="John Tech",
                signature=mock_sig,
                checklist=checklist,
                inspection_images=_vehicle_inspection_payload()["images"],
            )

        self.assertTrue(res)
        self.assertEqual(mock_cursor.executemany.call_count, 2)
        sql_arg, rows_arg = mock_cursor.executemany.call_args_list[0].args
        self.assertIn("INSERT INTO tbl_technicianinspectionchecklist", sql_arg)
        self.assertNotIn("PreparedByStaff", sql_arg)
        self.assertEqual(len(rows_arg), 2)
        self.assertTrue(all(len(row) == 7 for row in rows_arg))
        self.assertEqual(rows_arg[0][0], 42)
        self.assertEqual(rows_arg[0][1], "A1")
        self.assertEqual(rows_arg[0][5], 1)
        self.assertEqual(rows_arg[1][1], "E1")
        self.assertEqual(json.loads(rows_arg[1][6])[0]["value"], "6.5")
        image_sql, image_rows = mock_cursor.executemany.call_args_list[1].args
        self.assertIn("INSERT INTO tbl_vehicleinspectionimages", image_sql)
        self.assertIn("ON DUPLICATE KEY UPDATE", image_sql)
        self.assertEqual([row[1] for row in image_rows], ["image_1", "image_2", "image_3"])
        self.assertTrue(all(os.path.dirname(row[2]) == image_dir for row in image_rows))

    def test_save_update_vehicle_inspection_persists_checklist_and_image_paths(self):
        bma = _load_callables()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (42,)
        mock_cursor.fetchall.return_value = []
        with tempfile.TemporaryDirectory() as image_dir, \
             patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com", "role_id": 3}), \
             patch.object(bma, "_require_role"), \
             patch.object(bma, "VEHICLE_INSPECTION_IMAGE_DIR", image_dir), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            mock_db_cursor.return_value.__enter__.return_value = mock_cursor

            result = bma.save_update_vehicle_inspection(
                42, _vehicle_inspection_payload()
            )
            image_rows = mock_cursor.executemany.call_args_list[1].args[1]
            for row in image_rows:
                self.assertEqual(row[0], 42)
                self.assertTrue(os.path.isfile(row[2]))
                self.assertEqual(os.path.dirname(row[2]), image_dir)

        self.assertTrue(result["success"])
        self.assertEqual(mock_cursor.executemany.call_count, 2)
        calls = mock_cursor.executemany.call_args_list
        checklist_sql, checklist_rows = calls[0].args
        image_sql, image_rows = calls[1].args
        self.assertIn("INSERT INTO tbl_technicianinspectionchecklist", checklist_sql)
        self.assertNotIn("PreparedByStaff", checklist_sql)
        self.assertIn("ON DUPLICATE KEY UPDATE", checklist_sql)
        self.assertEqual(len(checklist_rows), 34)
        self.assertTrue(all(len(row) == 7 for row in checklist_rows))
        self.assertTrue(all(row[1].startswith("V-") for row in checklist_rows))
        self.assertIn("INSERT INTO tbl_vehicleinspectionimages", image_sql)
        self.assertIn("(JobCardRefID, ImageCode, ImagePath)", image_sql)
        self.assertIn("ON DUPLICATE KEY UPDATE", image_sql)
        self.assertEqual(len(image_rows), 3)
        fields_json = next(row[6] for row in checklist_rows if row[1] == "V-F1")
        saved_fields = {field["name"]: field["value"] for field in json.loads(fields_json)}
        self.assertEqual(
            saved_fields["date_picker_time_start"], "2026-11-08T09:15:00"
        )
        self.assertEqual(
            saved_fields["date_picker_time_end"], "2026-11-08T10:45:00"
        )

    def test_save_update_vehicle_inspection_rejects_incomplete_payload(self):
        bma = _load_callables()
        payload = _vehicle_inspection_payload()
        payload["textboxes"]["text_box_test_drive"] = " "
        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com", "role_id": 3}), \
             patch.object(bma, "_require_role"), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            with self.assertRaisesRegex(ValueError, "text_box_test_drive"):
                bma.save_update_vehicle_inspection(42, payload)

        mock_db_cursor.assert_not_called()

    def test_save_update_vehicle_inspection_rejects_unauthorized_user(self):
        bma = _load_callables()
        with patch("anvil.users.get_user", return_value={"email": "guest@bmaauto.com", "role_id": 99}), \
             patch.object(bma, "_require_role", side_effect=Exception("permission denied")):
            with self.assertRaisesRegex(Exception, "permission denied"):
                bma.save_update_vehicle_inspection(
                    42, _vehicle_inspection_payload()
                )

    def test_get_vehicle_inspection_data_returns_saved_fields_and_images(self):
        bma = _load_callables()
        mock_cursor = MagicMock()
        image_path = None
        with tempfile.TemporaryDirectory() as image_dir:
            image_path = os.path.join(image_dir, "inspection.png")
            with open(image_path, "wb") as image_file:
                image_file.write(b"\x89PNG\r\n\x1a\ninspection-image")
            mock_cursor.fetchall.side_effect = [
                [
                    (
                        "V-A1",
                        1,
                        None,
                        datetime.datetime(2026, 11, 9, 10, 0),
                        "Safety",
                        "Jack stands",
                    ),
                    (
                        "V-F1",
                        1,
                        json.dumps(
                            [
                                {
                                    "name": "text_box_voltage",
                                    "label": "Voltage",
                                    "value": "12.6",
                                },
                                {
                                    "name": "date_picker_time_start",
                                    "label": "Start",
                                    "value": "2026-11-09T09:15:00",
                                },
                            ]
                        ),
                        datetime.datetime(2026, 11, 9, 10, 0),
                        "Electrical",
                        "Battery voltage",
                    ),
                ],
                [("image_1", image_path)],
            ]
            saved_media = object()
            blob_media = MagicMock(return_value=saved_media)
            with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
                 patch.object(bma, "db_cursor") as mock_db_cursor, \
                 patch.object(bma, "VEHICLE_INSPECTION_IMAGE_DIR", image_dir), \
                 patch.object(bma.anvil, "BlobMedia", blob_media, create=True):
                mock_db_cursor.return_value.__enter__.return_value = mock_cursor

                result = bma.get_vehicle_inspection_data(42)

        self.assertTrue(result["checkboxes"]["chk_safety"])
        self.assertFalse(result["checkboxes"]["chk_jack"])
        self.assertEqual(result["textboxes"]["text_box_voltage"], "12.6")
        self.assertEqual(
            result["dates"]["date_picker_time_start"], "2026-11-09T09:15:00"
        )
        self.assertIs(result["images"]["image_1"], saved_media)
        self.assertIsNone(result["images"]["image_2"])
        queries = mock_cursor.execute.call_args_list
        self.assertIn("SELECT ItemCode, IsChecked, FieldsJSON", queries[0].args[0])
        self.assertEqual(queries[0].args[1], (42,))
        self.assertEqual(queries[1].args[1], (42,))
        blob_media.assert_called_once_with(
            "image/png",
            b"\x89PNG\r\n\x1a\ninspection-image",
            name="inspection.png",
        )

    def test_get_vehicle_inspection_data_rejects_invalid_jobcard_id(self):
        bma = _load_callables()
        with patch("anvil.users.get_user", return_value={"email": "tech@bmaauto.com"}), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            with self.assertRaisesRegex(ValueError, "job card ID"):
                bma.get_vehicle_inspection_data(0)

        mock_db_cursor.assert_not_called()

    def test_get_vehicle_inspection_data_requires_authenticated_user(self):
        bma = _load_callables()
        with patch("anvil.users.get_user", return_value=None), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            with self.assertRaisesRegex(Exception, "Authentication required"):
                bma.get_vehicle_inspection_data(42)

        mock_db_cursor.assert_not_called()

    def test_save_or_update_tech_portal_unauthorized_rejected(self):
        bma = _load_callables()
        with patch("anvil.users.get_user", return_value=None):
            with self.assertRaisesRegex(Exception, "Authentication required"):
                bma.saveOrUpdateTechnicianPortalDefectsAndRequestedParts(
                    jobcardID=42,
                    tech_notes="Notes",
                    defects="Defects",
                    requiredparts="None",
                    staff="John Tech",
                    signature=None,
                    checklist=[],
                )

    def test_get_jobcard_and_defect_details_returns_checklist(self):
        bma = _load_callables()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [("Tech note", "Brake defect", "Brake Pad - Qty: 1", "John Tech", b"sig", 42)],
            [
                (
                    "E1",
                    "E",
                    "E. BRAKES & SUSPENSION (CRITICAL)",
                    "Front pads thickness",
                    1,
                    json.dumps([{"name": "fpad", "label": "Front pads thickness (mm)", "value": "6.5"}]),
                )
            ],
        ]

        with patch("anvil.users.get_user", return_value={"email": "admin@bmaauto.com", "role_id": 1}), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            mock_db_cursor.return_value.__enter__.return_value = mock_cursor
            data = bma.get_jobcard_and_defect_details("JC-042")

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["Notes"], "Tech note")
        self.assertEqual(len(data[0]["Checklist"]), 1)
        self.assertEqual(data[0]["Checklist"][0]["id"], "E1")
        self.assertTrue(data[0]["Checklist"][0]["checked"])
        self.assertEqual(data[0]["Checklist"][0]["fields"][0]["value"], "6.5")
        checklist_sql, checklist_params = mock_cursor.execute.call_args_list[1].args
        self.assertIn("ItemCode NOT LIKE %s", checklist_sql)
        self.assertEqual(checklist_params, (42, "V-%"))

    def test_save_confirmation_details_upserts_verify_checklist_json(self):
        bma = _load_callables()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No existing row in tbl_completedjobcards

        mock_sig = MagicMock()
        mock_sig.get_bytes.return_value = b"sig-bytes"

        verify_payload = {
            "chk_torque": True,
            "chk_test": True,
            "chk_clean": True,
            "chk_old": True,
            "chk_explain": True,
            "next_service_date": "2027-04-28",
            "next_service_mileage": "125000",
            "time_start": "2026-10-28T09:00:00",
            "time_end": "2026-10-28T13:30:00",
            "efficiency": "95%",
        }

        with patch("anvil.users.get_user", return_value={"email": "advisor@bmaauto.com", "role_id": 1}), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            mock_db_cursor.return_value.__enter__.return_value = mock_cursor

            bma.saveConfirmationDetails(
                jobCardId=99,
                remarks="All checks verified",
                signature=mock_sig,
                dateCompleted="2026-10-28 14:00:00",
                verify_checklist=verify_payload,
            )

        last_call_sql, last_call_params = mock_cursor.execute.call_args[0]
        self.assertIn("INSERT INTO tbl_technicianinspectionchecklist", last_call_sql)
        self.assertNotIn("PreparedByStaff", last_call_sql)
        self.assertEqual(last_call_params[0], 99)
        self.assertEqual(len(last_call_params), 7)
        self.assertEqual(last_call_params[1], "F1")
        self.assertEqual(last_call_params[2], "F")
        self.assertEqual(last_call_params[5], 1)
        self.assertEqual(json.loads(last_call_params[6])["next_service_mileage"], "125000")

    def test_get_verify_task_checklist_returns_parsed_dict(self):
        bma = _load_callables()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            json.dumps({"chk_torque": True, "efficiency": "98%"}),
        )

        with patch("anvil.users.get_user", return_value={"email": "advisor@bmaauto.com", "role_id": 1}), \
             patch.object(bma, "db_cursor") as mock_db_cursor:
            mock_db_cursor.return_value.__enter__.return_value = mock_cursor
            res = bma.getVerifyTaskChecklist(99)

        self.assertIsNotNone(res)
        self.assertTrue(res["chk_torque"])
        self.assertEqual(res["efficiency"], "98%")


if __name__ == "__main__":
    unittest.main()
