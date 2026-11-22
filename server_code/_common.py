import anvil.server
import anvil.users
from anvil.tables import app_tables
import anvil.media
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import os
from contextlib import contextmanager
import re
import decimal
import base64
import html as html_module
from collections import defaultdict
from io import BytesIO
import datetime
import asyncio
import hashlib
import hmac
import json
import logging
import queue
import socket
import ssl
import sys
import tempfile
import threading
import time
import uuid

# Load environment variables from .env file
_app_root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_app_root_env):
    load_dotenv(dotenv_path=_app_root_env)
else:
    load_dotenv()

# Set your wkhtmltopdf path here (adjust for your system)
WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH")  # Windows path
_PDFKIT_CONFIG = None


def get_pdfkit():
    """Lazily import pdfkit so cold server boots do not pay its import cost."""
    import pdfkit
    return pdfkit


def get_pdfkit_config():
    """Lazily build and cache the pdfkit configuration on first PDF request."""
    global _PDFKIT_CONFIG
    if _PDFKIT_CONFIG is None:
        _PDFKIT_CONFIG = get_pdfkit().configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    return _PDFKIT_CONFIG


def get_bcrypt():
    """Lazily import bcrypt only for password hashing/reset operations."""
    import bcrypt
    return bcrypt


def get_websockets():
    """Lazily import websockets only when running or talking to the WS daemon."""
    import websockets
    return websockets


def __getattr__(name):
    """PEP 562 backward-compatible lazy attribute access for optional heavy dependencies."""
    if name == "pdfkit":
        return get_pdfkit()
    if name == "config":
        return get_pdfkit_config()
    if name == "bcrypt":
        return get_bcrypt()
    if name == "websockets":
        return get_websockets()
    if name in ("Workbook", "load_workbook"):
        import openpyxl
        return getattr(openpyxl, name)
    if name in ("Font", "PatternFill"):
        import openpyxl.styles as _styles
        return getattr(_styles, name)
    if name == "get_column_letter":
        from openpyxl.utils import get_column_letter
        return get_column_letter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
# Cache role names  
_ROLE_NAME_CACHE: dict[int, str] = {}
VEHICLE_INSPECTION_IMAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "VehicleInspectionImages",
)

# Connect to Anvil server
#anvil.server.connect(os.getenv("SERVER_UPLINK_KEY"))

# ---------------------------------------------------------------------------
# Connection pool — reuses TCP connections instead of opening one per request
# ---------------------------------------------------------------------------
_db_pool = pooling.MySQLConnectionPool(
    pool_name="bma_pool",
    pool_size=int(os.getenv("DB_POOL_SIZE", "16")),
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=str(os.getenv("DB_PASSWORD")),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
    auth_plugin=os.getenv("DB_AUTH_PLUGIN", "caching_sha2_password"),
)


def get_db_connection(max_retries=25, retry_delay=0.02):
    """Return a connection from the shared pool, retrying if pool is temporarily saturated."""
    for attempt in range(max_retries):
        try:
            return _db_pool.get_connection()
        except mysql.connector.errors.PoolError:
            if attempt == max_retries - 1:
                raise
            import time
            time.sleep(retry_delay)



# ---------------------------------------------------------------------------
# Authorization helpers
# ---------------------------------------------------------------------------

def _get_current_user():
    """Return the currently logged-in Anvil user, or raise if not logged in."""
    user = anvil.users.get_user()
    if user is None:
        raise Exception("Authentication required.")
    return user


def _require_role(*allowed_roles):
    user = _get_current_user()
    role_id = user["role_id"]
    if role_id not in _ROLE_NAME_CACHE:
        with db_cursor() as cursor:
            cursor.execute("SELECT Roles FROM tbl_roles WHERE ID = %s", (role_id,))
            row = cursor.fetchone()
        _ROLE_NAME_CACHE[role_id] = row[0] if row else None
    if _ROLE_NAME_CACHE[role_id] not in allowed_roles:
        raise Exception("You do not have permission to perform this action.")


# Context manager for DB cursor
@contextmanager
def db_cursor():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------------------------
# Thread-safe Server-Side TTL Lookup Cache (for slow-changing reference lists)
# ---------------------------------------------------------------------------
_LOOKUP_CACHE: dict[str, tuple[float, object]] = {}
_LOOKUP_CACHE_LOCK = threading.Lock()


def cached_lookup(key: str, loader, ttl_seconds: int = 300):
    """Return a cached lookup value if fresh, otherwise call loader() and cache it."""
    now = time.monotonic()
    with _LOOKUP_CACHE_LOCK:
        entry = _LOOKUP_CACHE.get(key)
        if entry is not None:
            expires_at, val = entry
            if now < expires_at:
                return val
    val = loader()
    with _LOOKUP_CACHE_LOCK:
        _LOOKUP_CACHE[key] = (now + ttl_seconds, val)
    return val


def invalidate_lookup_cache(*keys: str):
    """Invalidate specific lookup cache keys, or all keys if none provided."""
    with _LOOKUP_CACHE_LOCK:
        if not keys:
            _LOOKUP_CACHE.clear()
        else:
            for k in keys:
                _LOOKUP_CACHE.pop(k, None)


def invalidate_lookup_cache_prefix(*prefixes: str):
    """Invalidate all lookup cache keys starting with any of the given prefixes."""
    with _LOOKUP_CACHE_LOCK:
        to_delete = [
            k for k in _LOOKUP_CACHE
            if any(k.startswith(p) for p in prefixes)
        ]
        for k in to_delete:
            _LOOKUP_CACHE.pop(k, None)


# ---------------------------------------------------------------------------
# Non-blocking Realtime Event Bus Publisher (publishes to local WS on :8765)
# ---------------------------------------------------------------------------
_REALTIME_PUBLISH_QUEUE: "queue.Queue[dict]" = queue.Queue(maxsize=256)
_REALTIME_PUBLISHER_LOCK = threading.Lock()
_REALTIME_PUBLISHER_STARTED = False


def get_realtime_internal_secret() -> str:
    """Return shared secret used to authenticate loopback publish frames to port 8765."""
    explicit = (os.getenv("REALTIME_INTERNAL_SECRET") or "").strip()
    if explicit:
        return explicit
    seed = f"{os.getenv('DB_PASSWORD', '')}:{os.getenv('DB_NAME', 'BMALocal')}:bma_realtime_v1"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _send_realtime_payload_sync(payload: dict) -> bool:
    """Send a single internal_publish JSON payload to the local WS server."""
    ws_port = int(os.getenv("CHAT_WS_PORT", "8765").strip() or "8765")
    ssl_cert = (os.getenv("CHAT_WS_SSL_CERT") or "").strip()
    ssl_key = (os.getenv("CHAT_WS_SSL_KEY") or "").strip()
    use_tls = bool(ssl_cert and ssl_key and os.path.exists(ssl_cert) and os.path.exists(ssl_key))
    scheme = "wss" if use_tls else "ws"
    uri = f"{scheme}://127.0.0.1:{ws_port}"

    ssl_ctx = None
    if use_tls:
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

    async def _do_send():
        websockets = get_websockets()
        async with websockets.connect(uri, ssl=ssl_ctx, open_timeout=1.0, close_timeout=0.5) as ws:
            await ws.send(json.dumps(payload))
            try:
                await asyncio.wait_for(ws.recv(), timeout=0.5)
            except Exception:
                pass

    try:
        asyncio.run(_do_send())
        return True
    except Exception:
        return False


def _realtime_publisher_worker():
    """Background daemon draining _REALTIME_PUBLISH_QUEUE without blocking RPC calls."""
    while True:
        payload = _REALTIME_PUBLISH_QUEUE.get()
        try:
            _send_realtime_payload_sync(payload)
        except Exception:
            pass
        finally:
            _REALTIME_PUBLISH_QUEUE.task_done()


def _ensure_realtime_publisher_started():
    global _REALTIME_PUBLISHER_STARTED
    if _REALTIME_PUBLISHER_STARTED:
        return
    with _REALTIME_PUBLISHER_LOCK:
        if not _REALTIME_PUBLISHER_STARTED:
            t = threading.Thread(
                target=_realtime_publisher_worker,
                name="BMALocal-RealtimePublisher",
                daemon=True,
            )
            t.start()
            _REALTIME_PUBLISHER_STARTED = True


def publish_realtime_event(topic: str, action: str = "updated", entity_id=None, actor=None):
    """Fire-and-forget broadcast of a lightweight data_changed signal to connected clients."""
    if not topic or not isinstance(topic, str):
        return False
    if actor is None:
        try:
            user = anvil.users.get_user()
            if user:
                actor = user["email"] if not isinstance(user, dict) else user.get("email")
        except Exception:
            actor = None

    payload = {
        "type": "internal_publish",
        "secret": get_realtime_internal_secret(),
        "topic": topic.strip(),
        "action": (action or "updated").strip(),
        "entity_id": entity_id,
        "version": int(time.time() * 1000),
        "actor": actor or "",
    }
    try:
        _ensure_realtime_publisher_started()
        _REALTIME_PUBLISH_QUEUE.put_nowait(payload)
        return True
    except queue.Full:
        return False


__all__ = [name for name in globals() if not name.startswith("__")]
