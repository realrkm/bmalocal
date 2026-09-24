import pytest
from unittest.mock import patch
import server_code.BMALocal as bma

def test_calculate_invoice_breakdown_happy_path(mock_anvil_users):
    """Verify correct calculation of standard invoice breakdown with discount and VAT."""
    # Subtotal 10,000, 10% discount -> 9,000 net, 16% VAT -> 1,440 VAT, 10,440 total
    result = bma.calculate_invoice_breakdown(
        subtotal=10000.0,
        discount_percent=10.0,
        tax_rate_percent=16.0
    )
    assert result["subtotal"] == 10000.0
    assert result["discount_amount"] == 1000.0
    assert result["net_subtotal"] == 9000.0
    assert result["tax_amount"] == 1440.0
    assert result["total_amount"] == 10440.0

def test_calculate_invoice_breakdown_zero_discount(mock_anvil_users):
    """Verify boundary condition with 0% discount."""
    result = bma.calculate_invoice_breakdown(
        subtotal=5000.0,
        discount_percent=0.0,
        tax_rate_percent=16.0
    )
    assert result["discount_amount"] == 0.0
    assert result["total_amount"] == 5800.0

def test_calculate_invoice_breakdown_negative_subtotal(mock_anvil_users):
    """Verify input validation rejects negative subtotal."""
    with pytest.raises(ValueError, match="Subtotal cannot be negative"):
        bma.calculate_invoice_breakdown(
            subtotal=-100.0,
            discount_percent=0.0,
            tax_rate_percent=16.0
        )

def test_calculate_invoice_breakdown_invalid_discount_range(mock_anvil_users):
    """Verify input validation rejects discounts greater than 100% or negative."""
    with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
        bma.calculate_invoice_breakdown(
            subtotal=1000.0,
            discount_percent=105.0,
            tax_rate_percent=16.0
        )
    with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
        bma.calculate_invoice_breakdown(
            subtotal=1000.0,
            discount_percent=-5.0,
            tax_rate_percent=16.0
        )

def test_calculate_invoice_breakdown_unauthenticated():
    """Verify authentication gate: unauthenticated caller raises Exception."""
    with patch("anvil.users.get_user", return_value=None):
        with pytest.raises(Exception, match="Authentication required"):
            bma.calculate_invoice_breakdown(subtotal=1000.0)
