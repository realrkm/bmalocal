"""
End-to-End Test Suite for BMALocal Real-Time Walkie-Talkie & Chat (E2E-05).
Validates WebSocket handshake, presence broadcasting, bidirectional text exchange,
MySQL persistence, read receipt synchronization, message editing, and disconnect handling.
"""
import asyncio
import json
import ssl
import time
import pytest
import websockets
import server_code.BMALocal as bma

WS_URI = "wss://127.0.0.1:8765"


def get_test_ssl_context():
    """Create an SSL context that trusts local mkcert certificates."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


@pytest.fixture(scope="session", autouse=True)
def ensure_ws_server():
    """Ensure the BMALocal WebSocket daemon is running on port 8765."""
    if not bma.is_port_in_use("127.0.0.1", 8765):
        bma.start_websocket_server_thread()
        time.sleep(1.5)
    assert bma.is_port_in_use("127.0.0.1", 8765), "WebSocket server must be listening on port 8765"


def test_ws_connection_and_heartbeat():
    """Verify client can connect over TLS (WSS) and receive pong response from ping."""
    async def run():
        ssl_ctx = get_test_ssl_context()
        async with websockets.connect(WS_URI, ssl=ssl_ctx) as ws:
            await ws.send(json.dumps({"type": "ping"}))
            raw = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(raw)
            assert data["type"] == "pong"

    asyncio.run(run())


def test_user_join_and_history_sync():
    """Verify client sends join message, receives history, and triggers presence update."""
    async def run():
        ssl_ctx = get_test_ssl_context()
        async with websockets.connect(WS_URI, ssl=ssl_ctx) as ws:
            user_payload = {
                "email": "test.mechanic@bmaauto.com",
                "name": "Test Mechanic",
                "role_name": "Technician"
            }
            await ws.send(json.dumps({"type": "join", "user": user_payload}))

            # Expect first frame: history
            raw_hist = await asyncio.wait_for(ws.recv(), timeout=3.0)
            hist = json.loads(raw_hist)
            assert hist["type"] == "history"
            assert isinstance(hist["messages"], list)

            # Expect second frame: presence update including the joined user
            raw_pres = await asyncio.wait_for(ws.recv(), timeout=3.0)
            pres = json.loads(raw_pres)
            assert pres["type"] == "presence"
            assert pres["online_count"] >= 1
            emails = [u["email"] for u in pres["users"]]
            assert "test.mechanic@bmaauto.com" in emails

    asyncio.run(run())


async def recv_type(ws, target_type, timeout=4.0):
    """Read incoming frames until a message of target_type is encountered."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        remaining = max(0.1, deadline - time.time())
        raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
        data = json.loads(raw)
        if data.get("type") == target_type:
            return data
    raise TimeoutError(f"Did not receive frame of type {target_type}")


def test_bidirectional_chat_and_mysql_persistence():
    """
    Verify two concurrent clients (Technician and Manager) exchange real-time messages,
    and the message is durably written to MySQL tbl_walkietalkie_messages.
    """
    test_marker = f"[E2E-TEST] Bay 1 Status Update {int(time.time())}"
    created_msg_id = None

    async def run():
        nonlocal created_msg_id
        ssl_ctx = get_test_ssl_context()

        # Connect User A (Technician) and User B (Manager)
        async with websockets.connect(WS_URI, ssl=ssl_ctx) as ws_tech, \
                   websockets.connect(WS_URI, ssl=ssl_ctx) as ws_mgr:

            # Join User A
            await ws_tech.send(json.dumps({
                "type": "join",
                "user": {"email": "tech.e2e@bmaauto.com", "name": "Tech E2E", "role_name": "Technician"}
            }))
            await recv_type(ws_tech, "history")
            await recv_type(ws_tech, "presence")

            # Join User B
            await ws_mgr.send(json.dumps({
                "type": "join",
                "user": {"email": "mgr.e2e@bmaauto.com", "name": "Manager E2E", "role_name": "Manager"}
            }))
            await recv_type(ws_mgr, "history")
            await recv_type(ws_mgr, "presence")

            # User A transmits a real-time message
            await ws_tech.send(json.dumps({
                "type": "message",
                "text": test_marker
            }))

            # Both User A and User B receive the broadcasted message
            data_a = await recv_type(ws_tech, "message")
            assert data_a["message"]["message"] == test_marker
            assert data_a["message"]["sender_email"] == "tech.e2e@bmaauto.com"
            created_msg_id = data_a["message"]["id"]

            data_b = await recv_type(ws_mgr, "message")
            assert data_b["message"]["message"] == test_marker
            assert data_b["message"]["id"] == created_msg_id

            # User B marks the message as read
            await ws_mgr.send(json.dumps({
                "type": "mark_read",
                "last_read_id": created_msg_id,
                "user_email": "mgr.e2e@bmaauto.com"
            }))

            # Broadcast reads_updated should be delivered to User A
            read_data_a = await recv_type(ws_tech, "reads_updated")
            assert read_data_a["last_read_id"] == created_msg_id
            assert read_data_a["user_email"] == "mgr.e2e@bmaauto.com"

    asyncio.run(run())

    # Verify MySQL persistence directly
    assert created_msg_id is not None
    try:
        with bma.db_cursor() as cursor:
            cursor.execute(
                "SELECT id, sender_email, message FROM tbl_walkietalkie_messages WHERE id = %s",
                (created_msg_id,)
            )
            row = cursor.fetchone()
            assert row is not None, "Message must be saved to MySQL database"
            assert row[0] == created_msg_id
            assert row[1] == "tech.e2e@bmaauto.com"
            assert row[2] == test_marker
    finally:
        with bma.db_cursor() as cursor:
            cursor.execute("DELETE FROM tbl_walkietalkie_messages WHERE id = %s", (created_msg_id,))


def test_message_edit_workflow():
    """Verify sender can edit message within 15-minute window and broadcast change."""
    created_id = None
    initial_text = f"[E2E-TEST] Initial text {int(time.time())}"
    updated_text = f"[E2E-TEST] Corrected text {int(time.time())}"

    async def run():
        nonlocal created_id
        ssl_ctx = get_test_ssl_context()
        async with websockets.connect(WS_URI, ssl=ssl_ctx) as ws:
            # Join as sender
            await ws.send(json.dumps({
                "type": "join",
                "user": {"email": "editor@bmaauto.com", "name": "Editor", "role_name": "Admin"}
            }))
            await asyncio.wait_for(ws.recv(), timeout=3.0)  # history
            await asyncio.wait_for(ws.recv(), timeout=3.0)  # presence

            # Send initial message
            await ws.send(json.dumps({"type": "message", "text": initial_text}))
            msg_frame = json.loads(await asyncio.wait_for(ws.recv(), timeout=3.0))
            created_id = msg_frame["message"]["id"]

            # Edit the message
            await ws.send(json.dumps({
                "type": "edit_message",
                "message_id": created_id,
                "sender_email": "editor@bmaauto.com",
                "new_text": updated_text
            }))

            edit_frame = json.loads(await asyncio.wait_for(ws.recv(), timeout=3.0))
            assert edit_frame["type"] == "message_edited"
            assert edit_frame["message"]["id"] == created_id
            assert edit_frame["message"]["message"] == updated_text
            assert edit_frame["message"]["is_edited"] is True

    asyncio.run(run())

    # Verify MySQL reflects the edit
    try:
        with bma.db_cursor() as cursor:
            cursor.execute(
                "SELECT message, is_edited FROM tbl_walkietalkie_messages WHERE id = %s",
                (created_id,)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == updated_text
            assert bool(row[1]) is True
    finally:
        with bma.db_cursor() as cursor:
            cursor.execute("DELETE FROM tbl_walkietalkie_messages WHERE id = %s", (created_id,))


def test_client_disconnect_presence_notification():
    """Verify remaining clients receive presence update when a client disconnects."""
    async def run():
        ssl_ctx = get_test_ssl_context()
        ws_listener = await websockets.connect(WS_URI, ssl=ssl_ctx)
        ws_temporary = await websockets.connect(WS_URI, ssl=ssl_ctx)

        try:
            # Join listener
            await ws_listener.send(json.dumps({
                "type": "join",
                "user": {"email": "listener@bmaauto.com", "name": "Listener", "role_name": "Cashier"}
            }))
            await asyncio.wait_for(ws_listener.recv(), timeout=3.0)  # history
            await asyncio.wait_for(ws_listener.recv(), timeout=3.0)  # presence

            # Join temporary user
            await ws_temporary.send(json.dumps({
                "type": "join",
                "user": {"email": "temp.user@bmaauto.com", "name": "Temp", "role_name": "Staff"}
            }))
            await asyncio.wait_for(ws_temporary.recv(), timeout=3.0)  # history
            await asyncio.wait_for(ws_temporary.recv(), timeout=3.0)  # presence
            # ws_listener receives presence update with 2 users
            pres_2 = json.loads(await asyncio.wait_for(ws_listener.recv(), timeout=3.0))
            assert pres_2["type"] == "presence"
            assert "temp.user@bmaauto.com" in [u["email"] for u in pres_2["users"]]

            # Disconnect temporary user
            await ws_temporary.close()

            # ws_listener should receive a new presence update without temp.user
            pres_1 = json.loads(await asyncio.wait_for(ws_listener.recv(), timeout=3.0))
            assert pres_1["type"] == "presence"
            emails_after = [u["email"] for u in pres_1["users"]]
            assert "temp.user@bmaauto.com" not in emails_after
        finally:
            await ws_listener.close()

    asyncio.run(run())
