import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Ensure BMALocal root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture(autouse=True)
def mock_anvil_users():
    """Mock anvil.users to simulate an authenticated Admin user for unit tests."""
    with patch("anvil.users.get_user") as mock_get_user:
        mock_get_user.return_value = {
            "email": "admin@bmaauto.com",
            "role_id": 1,
        }
        yield mock_get_user
