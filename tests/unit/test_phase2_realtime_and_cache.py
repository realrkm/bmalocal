import asyncio
import json
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import server_code.BMALocal as bma
from server_code import _common, invoices, job_cards, notifications, realtime, users

REPO_ROOT = Path(__file__).resolve().parents[2]


class _FakeWebSocket:
    def __init__(self, remote_address=("127.0.0.1", 55000), incoming=None):
        self.remote_address = remote_address
        self._incoming = list(incoming or [])
        self.sent = []
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._incoming:
            raise StopAsyncIteration
        return self._incoming.pop(0)

    async def send(self, payload):
        self.sent.append(payload)


def test_validate_internal_publish_security_gates():
    secret = _common.get_realtime_internal_secret()
    ws_local = _FakeWebSocket(("127.0.0.1", 50001))
    ws_remote = _FakeWebSocket(("192.168.1.55", 50001))

    assert realtime._validate_internal_publish(ws_local, {"secret": secret, "topic": "jobcards"}) is True
    assert realtime._validate_internal_publish(ws_remote, {"secret": secret, "topic": "jobcards"}) is False
    assert realtime._validate_internal_publish(ws_local, {"secret": "wrong-secret", "topic": "jobcards"}) is False
    assert realtime._validate_internal_publish(ws_local, {"secret": secret, "topic": "bad topic!"}) is False
    assert realtime._validate_internal_publish(ws_local, {"secret": secret, "topic": ""}) is False


def test_chat_handler_internal_publish_broadcasts_data_changed_and_skips_presence():
    secret = _common.get_realtime_internal_secret()
    subscriber_ws = _FakeWebSocket(("192.168.1.20", 60000))
    publisher_ws = _FakeWebSocket(
        ("127.0.0.1", 60001),
        incoming=[
            json.dumps({
                "type": "internal_publish",
                "secret": secret,
                "topic": "jobcards",
                "action": "status_updated",
                "entity_id": 42,
                "actor": "tech@bmaauto.com",
            })
        ],
    )

    realtime.connected_clients.clear()
    realtime.connected_clients[subscriber_ws] = {"email": "manager@bmaauto.com", "role_name": "Manager"}

    with patch.object(realtime, "send_presence", new_callable=AsyncMock) as mock_presence:
        asyncio.run(realtime.chat_handler(publisher_ws))

    mock_presence.assert_not_awaited()
    assert publisher_ws not in realtime.connected_clients
    assert len(publisher_ws.sent) == 1
    assert json.loads(publisher_ws.sent[0]) == {"type": "publish_ack", "ok": True}

    assert len(subscriber_ws.sent) == 1
    evt = json.loads(subscriber_ws.sent[0])
    assert evt["type"] == "data_changed"
    assert evt["topic"] == "jobcards"
    assert evt["action"] == "status_updated"
    assert evt["entity_id"] == 42
    assert evt["actor"] == "tech@bmaauto.com"
    realtime.connected_clients.clear()


def test_chat_handler_rejects_unauthorized_internal_publish():
    subscriber_ws = _FakeWebSocket(("192.168.1.20", 60000))
    attacker_ws = _FakeWebSocket(
        ("192.168.1.99", 60002),
        incoming=[
            json.dumps({
                "type": "internal_publish",
                "secret": _common.get_realtime_internal_secret(),
                "topic": "jobcards",
            })
        ],
    )

    realtime.connected_clients.clear()
    realtime.connected_clients[subscriber_ws] = {"email": "manager@bmaauto.com", "role_name": "Manager"}

    asyncio.run(realtime.chat_handler(attacker_ws))

    assert len(subscriber_ws.sent) == 0
    ack = json.loads(attacker_ws.sent[0])
    assert ack["type"] == "publish_ack"
    assert ack["ok"] is False
    realtime.connected_clients.clear()


def test_mutations_publish_realtime_events():
    cursor = MagicMock()
    cursor.fetchone.return_value = ("JC-001",)

    with patch.object(job_cards, "_get_current_user"), \
         patch.object(job_cards, "db_cursor") as jc_db, \
         patch.object(job_cards, "publish_realtime_event") as jc_pub:
        jc_db.return_value.__enter__.return_value = cursor
        job_cards.updateJobCardStatus(101, "In Service")
        jc_pub.assert_called_once_with("jobcards", "status_updated", entity_id=101)

    with patch.object(notifications, "_get_current_user"), \
         patch.object(notifications, "db_cursor") as n_db, \
         patch.object(notifications, "getNotificationJobCardRef", return_value="JC-101"), \
         patch.object(notifications, "publish_realtime_event") as n_pub:
        n_db.return_value.__enter__.return_value = cursor
        notifications.publish_role_notification(101, "Ready")
        n_pub.assert_called_once_with("notifications", "created", entity_id=101)

    with patch.object(invoices, "_get_current_user"), \
         patch.object(invoices, "db_cursor") as inv_db, \
         patch.object(invoices, "publish_realtime_event") as inv_pub:
        inv_db.return_value.__enter__.return_value = cursor
        invoices.update_invoice_status(101)
        assert inv_pub.call_count == 2
        inv_pub.assert_any_call("payments", "invoice_paid", entity_id=101)
        inv_pub.assert_any_call("jobcards", "invoice_paid", entity_id=101)


def test_get_users_eliminates_n_plus_1_role_queries():
    cursor = MagicMock()
    cursor.fetchall.return_value = [(1, "Administrator"), (2, "Technician")]
    fake_users = [
        {"email": f"u{i}@bmaauto.com", "last_login": None, "signed_up": None, "role_id": 1 if i % 2 == 0 else 2, "enabled": True, "n_password_failures": 0}
        for i in range(5)
    ]

    fake_tables = MagicMock()
    fake_tables.users.search.return_value = fake_users

    with patch.object(users, "_require_role"), \
         patch.object(users, "db_cursor") as u_db, \
         patch.object(users, "app_tables", fake_tables):
        u_db.return_value.__enter__.return_value = cursor
        result = users.getUsers()

    assert len(result) == 5
    assert result[0]["role"] == "Administrator"
    assert result[1]["role"] == "Technician"
    # Must query tbl_roles only ONCE instead of 5 times
    assert cursor.execute.call_count == 1
    assert "SELECT ID, Roles FROM tbl_roles" in cursor.execute.call_args[0][0]


def test_mod_cache_topic_invalidation_and_clear(monkeypatch):
    fake_anvil = types.ModuleType("anvil")
    fake_js = types.ModuleType("anvil.js")
    fake_js.window = types.SimpleNamespace(bmaRealtime=None)
    fake_anvil.js = fake_js
    monkeypatch.setitem(sys.modules, "anvil", fake_anvil)
    monkeypatch.setitem(sys.modules, "anvil.js", fake_js)

    import importlib
    if "client_code.ModCache" in sys.modules:
        del sys.modules["client_code.ModCache"]
    mod_cache = importlib.import_module("client_code.ModCache")
    mod_cache.clear()

    calls = {"jc": 0, "inv": 0}

    def fetch_jc():
        calls["jc"] += 1
        return ["jc1", "jc2"]

    def fetch_inv():
        calls["inv"] += 1
        return ["part1"]

    assert mod_cache.get_or_fetch("jc_list", fetch_jc, topic="jobcards") == ["jc1", "jc2"]
    assert mod_cache.get_or_fetch("jc_list", fetch_jc, topic="jobcards") == ["jc1", "jc2"]
    assert calls["jc"] == 1

    assert mod_cache.get_or_fetch("parts", fetch_inv, topic="inventory") == ["part1"]
    assert calls["inv"] == 1

    # Invalidating jobcards leaves inventory intact
    mod_cache.invalidate_topic("jobcards")
    assert mod_cache.get_cached("jc_list") is None
    assert mod_cache.get_cached("parts") == ["part1"]

    mod_cache.clear()
    assert mod_cache.get_cached("parts") is None


def test_walkietalkie_js_exposes_realtime_bus_and_backoff():
    js_text = (REPO_ROOT / "theme" / "assets" / "walkietalkie.js").read_text(encoding="utf-8")
    assert "window.bmaRealtime" in js_text
    assert 'data.type === "data_changed"' in js_text
    assert "Math.pow(2, reconnectAttempts)" in js_text


def test_contacts_bookings_and_inventory_mutations_publish_realtime_events():
    from server_code import bookings, inventory, people

    cursor = MagicMock()
    cursor.lastrowid = 88

    with patch.object(people, "_get_current_user"), \
         patch.object(people, "db_cursor") as p_db, \
         patch.object(people, "publish_realtime_event") as p_pub:
        p_db.return_value.__enter__.return_value = cursor
        people.save_client_data("Jane Doe", "0712345678", "Nairobi", "jane@example.com", "")
        p_pub.assert_called_once_with("contacts", "client_created", entity_id=88)

    with patch.object(bookings, "_get_current_user"), \
         patch.object(bookings, "db_cursor") as b_db, \
         patch.object(bookings, "publish_realtime_event") as b_pub:
        b_db.return_value.__enter__.return_value = cursor
        assert bookings.saveBookingDetails(1, "KAA 123A", "2026-12-01 10:00:00", "Service") is True
        b_pub.assert_called_once_with("bookings", "booking_created", entity_id=88)

    with patch.object(inventory, "_get_current_user"), \
         patch.object(inventory, "db_cursor") as i_db, \
         patch.object(inventory, "publish_realtime_event") as i_pub:
        i_db.return_value.__enter__.return_value = cursor
        inventory.addStock("2026-12-01", 2, 15, 10, 500)
        i_pub.assert_called_once_with("inventory", "stock_added", entity_id=15)
