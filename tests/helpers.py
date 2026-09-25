"""
Helper utilities and test calculation functions for BMALocal test suites.
Separated from server_code/BMALocal.py to isolate testing utilities.
"""
from server_code.BMALocal import _get_current_user


def calculate_invoice_breakdown(subtotal, discount_percent=0.0, tax_rate_percent=16.0):
    """
    Calculate financial breakdown for invoices and quotes with VAT and discount.

    Args:
        subtotal (float): Gross items subtotal before discount/tax.
        discount_percent (float, optional): Discount percentage (0.0 to 100.0). Defaults to 0.0.
        tax_rate_percent (float, optional): Tax rate percentage (e.g. 16.0% VAT). Defaults to 16.0.
    Returns:
        dict: {
            "subtotal": float,
            "discount_amount": float,
            "net_subtotal": float,
            "tax_amount": float,
            "total_amount": float
        }
    """
    _get_current_user()

    try:
        subtotal_val = float(subtotal)
        discount_val = float(discount_percent)
        tax_val = float(tax_rate_percent)
    except (TypeError, ValueError):
        raise ValueError("Subtotal, discount, and tax rate must be valid numbers.")

    if subtotal_val < 0:
        raise ValueError("Subtotal cannot be negative.")
    if not (0.0 <= discount_val <= 100.0):
        raise ValueError("Discount percent must be between 0 and 100.")
    if tax_val < 0:
        raise ValueError("Tax rate cannot be negative.")

    discount_amount = round(subtotal_val * (discount_val / 100.0), 2)
    net_subtotal = round(subtotal_val - discount_amount, 2)
    tax_amount = round(net_subtotal * (tax_val / 100.0), 2)
    total_amount = round(net_subtotal + tax_amount, 2)

    return {
        "subtotal": subtotal_val,
        "discount_amount": discount_amount,
        "net_subtotal": net_subtotal,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
    }
