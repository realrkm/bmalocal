import pytest
from unittest.mock import patch, MagicMock
from server_code.modAnalytics import get_stats, _is_private_ip, fe_keepalive

def test_is_private_ip():
    assert _is_private_ip("127.0.0.1") is True
    assert _is_private_ip("192.168.1.100") is True
    assert _is_private_ip("10.0.0.5") is True
    assert _is_private_ip(None) is True
    assert _is_private_ip("invalid-ip") is True
    assert _is_private_ip("8.8.8.8") is False

def test_fe_keepalive():
    assert fe_keepalive() == "ok"

def test_get_stats_synchronous_success(mock_anvil_users):
    mock_app_tables = MagicMock()
    with patch("anvil.server.context.client") as mock_client, \
         patch("server_code.modAnalytics.app_tables", mock_app_tables):
        mock_client.ip = "192.168.100.12"
        mock_client.location = None
        mock_client.type = "browser"
        
        result = get_stats("Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        assert result == "ok"
        assert mock_app_tables.tbl_stats.add_row.called
