import pytest
import datetime
import re
from unittest.mock import MagicMock, patch
import server_code.BMALocal as bma

def test_get_chat_user_profile(mock_anvil_users):
    """Verify initials and profile formatting for chat user."""
    with patch("server_code.BMALocal.db_cursor") as mock_cursor_ctx:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Admin",)
        mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
        
        prof = bma.get_chat_user_profile()
        assert prof["email"] == "admin@bmaauto.com"
        assert prof["role_name"] == "Admin"
        assert prof["initials"] == "AD"

def test_chat_initials_multi_part():
    """Verify initials derivation for multiple word names in email prefix."""
    email = "john.doe@bmaauto.com"
    prefix = email.split("@")[0]
    parts = [p for p in re.split(r"[._\-+]", prefix) if p]
    inits = (parts[0][0] + parts[1][0]).upper()
    assert inits == "JD"
