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
import pdfkit
import decimal
import base64
import html as html_module
from collections import defaultdict
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from io import BytesIO
import datetime
import bcrypt
import asyncio
import json
import logging
import socket
import ssl
import sys
import tempfile
import threading
import uuid
import websockets

# Load environment variables from .env file
_app_root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_app_root_env):
    load_dotenv(dotenv_path=_app_root_env)
else:
    load_dotenv()

# Set your wkhtmltopdf path here (adjust for your system)
WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH")  # Windows path
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
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

__all__ = [name for name in globals() if not name.startswith("__")]
