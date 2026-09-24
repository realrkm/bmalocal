import pytest
from unittest.mock import MagicMock, patch
import server_code.BMALocal as bma

def test_get_current_user_authenticated():
    """Verify _get_current_user returns user object when session is active."""
    with patch("anvil.users.get_user") as mock_user:
        mock_user.return_value = {"email": "test@bmaauto.com", "role_id": 1}
        user = bma._get_current_user()
        assert user["email"] == "test@bmaauto.com"

def test_get_current_user_unauthenticated():
    """Verify _get_current_user raises Exception when not logged in."""
    with patch("anvil.users.get_user", return_value=None):
        with pytest.raises(Exception, match="Authentication required"):
            bma._get_current_user()

def test_require_role_authorized():
    """Verify _require_role succeeds when user role is in allowed list."""
    with patch("anvil.users.get_user") as mock_user, \
         patch("server_code.BMALocal.db_cursor") as mock_cursor_ctx:
        mock_user.return_value = {"email": "admin@bmaauto.com", "role_id": 1}
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Admin",)
        mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
        
        user = bma._require_role("Admin", "Manager")
        assert user["role_id"] == 1

def test_require_role_unauthorized():
    """Verify _require_role raises Exception when user role is not allowed."""
    with patch("anvil.users.get_user") as mock_user, \
         patch("server_code.BMALocal.db_cursor") as mock_cursor_ctx:
        mock_user.return_value = {"email": "tech@bmaauto.com", "role_id": 3}
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Technician",)
        mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
        
        with pytest.raises(Exception, match="You do not have permission"):
            bma._require_role("Admin", "Manager")
