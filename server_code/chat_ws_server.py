"""
BMALocal Real-Time Walkie Talkie Chat WebSocket Server
Uses Python's `websockets` library and MySQL persistence.
Loads connection configuration strictly from .env.
Listens on ws://127.0.0.1:8765 (configurable via CHAT_WS_PORT/CHAT_WS_HOST)
"""

import asyncio
import json
import os
import re
import ssl
from datetime import datetime
from dotenv import load_dotenv
import mysql.connector
import websockets

# Load .env file from the application root (BMALocal) or current directory
_app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_path = os.path.join(_app_root, ".env")
if not os.path.exists(_env_path):
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_env_path)

# Strictly read MySQL connection settings from .env without fallbacks
DB_HOST = os.environ["DB_HOST"].strip()
DB_PORT = int(os.environ["DB_PORT"].strip())
DB_USER = os.environ["DB_USER"].strip()
DB_PASSWORD = os.environ["DB_PASSWORD"].strip()
DB_NAME = os.environ["DB_NAME"].strip()
DB_AUTH_PLUGIN = os.environ.get("DB_AUTH_PLUGIN", "").strip() or None

# Strictly read WebSocket server settings from .env without fallbacks
WS_HOST = os.environ["CHAT_WS_HOST"].strip()
WS_PORT = int(os.environ["CHAT_WS_PORT"].strip())

# Optional SSL certificate settings for WSS (required when application is served over HTTPS)
SSL_CERT_FILE = os.environ.get("CHAT_WS_SSL_CERT", "").strip()
SSL_KEY_FILE = os.environ.get("CHAT_WS_SSL_KEY", "").strip()


def get_db_connection():
    kwargs = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME,
    }
    if DB_AUTH_PLUGIN:
        kwargs["auth_plugin"] = DB_AUTH_PLUGIN
    return mysql.connector.connect(**kwargs)


def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tbl_walkietalkie_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_email VARCHAR(255) NOT NULL,
                role_name VARCHAR(100) DEFAULT '',
                message TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_edited TINYINT(1) NOT NULL DEFAULT 0
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except mysql.connector.Error as err:
        # User 'office' may not have CREATE privilege if table was created by root/admin
        if "command denied" in str(err).lower() or getattr(err, "errno", 0) == 1142:
            print("[*] Note: CREATE privilege omitted for DB user. Verifying existing table...")
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM tbl_walkietalkie_messages LIMIT 1")
                cur.fetchall()
                cur.close()
                conn.close()
                print("[*] tbl_walkietalkie_messages verified.")
            except Exception as e:
                print(f"[!] Warning checking table: {e}")
        else:
            raise


def compute_initials(email):
    clean = (email or "").strip().lower()
    if "@" in clean:
        prefix = clean.split("@")[0]
        parts = [p for p in re.split(r"[._\-+]", prefix) if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        elif len(parts) == 1 and len(parts[0]) >= 2:
            return parts[0][:2].upper()
        elif parts:
            return parts[0][0].upper()
    elif clean:
        parts = clean.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        elif parts:
            return parts[0][:2].upper()
    return "U"


def format_row(row):
    msg_id = row[0]
    sender_email = row[1]
    role_name = row[2]
    message = row[3]
    created_at = row[4]
    is_edited = bool(row[5]) if len(row) > 5 and row[5] else False

    dt = None
    if isinstance(created_at, datetime):
        dt = created_at
    elif isinstance(created_at, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                dt = datetime.strptime(created_at, fmt)
                break
            except ValueError:
                pass
    if not dt:
        dt = datetime.now()

    time_str = dt.strftime("%I:%M %p")
    today = datetime.now().date()
    msg_date = dt.date()
    if msg_date == today:
        date_group = "Today"
    elif (today - msg_date).days == 1:
        date_group = "Yesterday"
    else:
        date_group = dt.strftime("%a, %b %d, %Y")

    return {
        "id": msg_id,
        "sender_email": sender_email,
        "role_name": role_name or "",
        "initials": compute_initials(sender_email),
        "message": message,
        "created_at": dt.isoformat(),
        "time": time_str,
        "date_group": date_group,
        "is_edited": is_edited,
    }


def get_history(limit=50):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, sender_email, role_name, message, created_at, is_edited
        FROM tbl_walkietalkie_messages
        ORDER BY id DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    rows.reverse()
    return [format_row(r) for r in rows]


def insert_message(user_data, text):
    sender_email = (user_data.get("email") or user_data.get("sender_email") or "").strip().lower()
    role_name = user_data.get("role_name") or user_data.get("role") or ""

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tbl_walkietalkie_messages (sender_email, role_name, message, is_edited)
        VALUES (%s, %s, %s, 0)
    """, (sender_email, role_name, text))
    new_id = cur.lastrowid
    conn.commit()

    cur.execute("""
        SELECT id, sender_email, role_name, message, created_at, is_edited
        FROM tbl_walkietalkie_messages
        WHERE id = %s
    """, (new_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    return format_row(row)


def edit_message(msg_id, user_email, new_text):
    """
    Update message if sender matches and created_at is within 15 minutes.
    Returns formatted row or None if unauthorized or expired.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, sender_email, role_name, message, created_at, is_edited
        FROM tbl_walkietalkie_messages
        WHERE id = %s
    """, (msg_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None

    sender_email = (row[1] or "").strip().lower()
    if sender_email != user_email.strip().lower():
        cur.close()
        conn.close()
        return None

    created_at = row[4]
    dt = None
    if isinstance(created_at, datetime):
        dt = created_at
    elif isinstance(created_at, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                dt = datetime.strptime(created_at, fmt)
                break
            except ValueError:
                pass
    if not dt:
        dt = datetime.now()

    # 15 minutes limit (900 seconds)
    elapsed_sec = (datetime.now() - dt).total_seconds()
    if elapsed_sec > 15 * 60 or elapsed_sec < -60:
        cur.close()
        conn.close()
        return None

    cur.execute("""
        UPDATE tbl_walkietalkie_messages
        SET message = %s, is_edited = 1
        WHERE id = %s
    """, (new_text, msg_id))
    conn.commit()

    cur.execute("""
        SELECT id, sender_email, role_name, message, created_at, is_edited
        FROM tbl_walkietalkie_messages
        WHERE id = %s
    """, (msg_id,))
    updated_row = cur.fetchone()
    cur.close()
    conn.close()

    return format_row(updated_row)


# Active connected WebSocket clients: {websocket: user_data_dict}
connected_clients = {}


async def broadcast(message_dict):
    if not connected_clients:
        return
    payload = json.dumps(message_dict)
    tasks = []
    for ws in list(connected_clients.keys()):
        try:
            tasks.append(ws.send(payload))
        except Exception:
            pass
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


def get_unique_online_users():
    """Return a deduplicated list of currently logged-in users by email."""
    unique_users = {}
    for ws, u in list(connected_clients.items()):
        # Clean up any closed or closing sockets
        if getattr(ws, "closed", False):
            connected_clients.pop(ws, None)
            continue
        email = (u.get("email") or "").strip().lower()
        if email and "@" in email and email != "guest":
            unique_users[email] = {
                "name": u.get("name", "User"),
                "email": email,
                "role": u.get("role_name", ""),
            }
    return list(unique_users.values())


async def send_presence():
    users_online = get_unique_online_users()
    online_count = len(users_online)
    print(f"[*] Presence update: {online_count} online -> {[u['email'] for u in users_online]}")
    await broadcast({
        "type": "presence",
        "online_count": online_count,
        "users": users_online,
    })


async def chat_handler(websocket):
    current_user = {
        "email": "",
        "role_name": "User",
        "initials": "U",
    }
    connected_clients[websocket] = current_user

    try:
        async for raw_msg in websocket:
            try:
                data = json.loads(raw_msg)
            except Exception:
                continue

            msg_type = data.get("type")

            if msg_type == "join":
                user_info = data.get("user", {})
                email = (user_info.get("email") or "").strip().lower()
                if email and "@" in email and email != "guest":
                    current_user.update(user_info)
                    current_user["email"] = email
                    if not current_user.get("initials"):
                        current_user["initials"] = compute_initials(email)
                    connected_clients[websocket] = current_user
                else:
                    current_user["email"] = ""
                    connected_clients[websocket] = current_user

                # Send history
                history = get_history(limit=100)
                await websocket.send(json.dumps({
                    "type": "history",
                    "messages": history,
                }))

                # Broadcast presence
                await send_presence()

            elif msg_type in ("leave", "logout"):
                current_user["email"] = ""
                current_user["name"] = "Guest"
                connected_clients.pop(websocket, None)
                await send_presence()
                try:
                    await websocket.close()
                except Exception:
                    pass
                break

            elif msg_type == "message":
                text = (data.get("text") or "").strip()
                if not text:
                    continue
                formatted_msg = insert_message(current_user, text)
                await broadcast({
                    "type": "message",
                    "message": formatted_msg,
                })

            elif msg_type == "edit_message":
                msg_id = data.get("message_id")
                new_text = (data.get("new_text") or "").strip()
                user_email = (current_user.get("email") or data.get("sender_email") or "").strip().lower()

                if not msg_id or not new_text:
                    continue

                if not user_email:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "User not authenticated to edit messages.",
                    }))
                    continue

                if not current_user.get("email"):
                    current_user["email"] = user_email

                updated_msg = edit_message(msg_id, user_email, new_text)
                if updated_msg:
                    print(f"[*] Message #{msg_id} edited by {user_email}: {new_text}")
                    await broadcast({
                        "type": "message_edited",
                        "message": updated_msg,
                    })
                else:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Message can only be edited by the sender within 15 minutes.",
                    }))

            elif msg_type == "get_history":
                history = get_history(limit=100)
                await websocket.send(json.dumps({
                    "type": "history",
                    "messages": history,
                }))

            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.pop(websocket, None)
        await send_presence()


async def main():
    init_db()
    ssl_context = None
    protocol = "ws"
    if SSL_CERT_FILE and SSL_KEY_FILE:
        if os.path.exists(SSL_CERT_FILE) and os.path.exists(SSL_KEY_FILE):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(SSL_CERT_FILE, keyfile=SSL_KEY_FILE)
            protocol = "wss"
            print(f"[*] SSL/TLS enabled for WSS using cert: {SSL_CERT_FILE}")
        else:
            print(f"[!] Warning: SSL certificate or key file not found. Starting in plain ws:// mode.")

    print(f"[*] Walkie Talkie WebSocket Server starting on {protocol}://{WS_HOST}:{WS_PORT} (MySQL persistence)...")
    async with websockets.serve(chat_handler, WS_HOST, WS_PORT, ssl=ssl_context):
        print(f"[+] Server is listening on {protocol}://{WS_HOST}:{WS_PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Chat server stopped.")
