import json
import sys
import types
import unittest
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


class TestTechnicianChecklist(unittest.TestCase):
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

        with patch("anvil.users.get_user", return_value={"email": "admin@bmaauto.com", "role_id": 1}), \
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
            )

        self.assertTrue(res)
        self.assertEqual(mock_cursor.executemany.call_count, 1)
        sql_arg, rows_arg = mock_cursor.executemany.call_args[0]
        self.assertIn("INSERT INTO tbl_technicianinspectionchecklist", sql_arg)
        self.assertEqual(len(rows_arg), 2)
        self.assertEqual(rows_arg[0][0], 42)
        self.assertEqual(rows_arg[0][1], "A1")
        self.assertEqual(rows_arg[0][5], 1)
        self.assertEqual(rows_arg[1][1], "E1")
        self.assertEqual(json.loads(rows_arg[1][6])[0]["value"], "6.5")

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


if __name__ == "__main__":
    unittest.main()

