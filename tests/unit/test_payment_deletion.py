import datetime
from unittest.mock import MagicMock, patch

import pytest

import server_code.BMALocal as bma


def test_delete_payment_removes_record_and_recalculates_balances():
    cursor = MagicMock()
    cursor.fetchone.side_effect = [(42,), (100,)]
    cursor.fetchall.return_value = [(20, 40, 0), (21, 20, 0)]
    cursor.rowcount = 1

    with patch.object(bma, "_require_role") as require_role, patch.object(
        bma, "db_cursor"
    ) as db_cursor:
        db_cursor.return_value.__enter__.return_value = cursor

        result = bma.delete_payment(17)

    require_role.assert_called_once_with("Admin")
    assert result == {"success": True, "payment_id": 17, "jobcard_id": 42}
    assert any(
        call.args[0] == "DELETE FROM tbl_payments WHERE ID = %s"
        and call.args[1] == (17,)
        for call in cursor.execute.call_args_list
    )
    cursor.executemany.assert_called_once()
    assert cursor.executemany.call_args.args[1] == [(60, 20), (40, 21)]
    assert any(
        "SET Status = CASE" in call.args[0]
        and call.args[1] == (60, 100, 42)
        for call in cursor.execute.call_args_list
    )


@pytest.mark.parametrize("payment_id", [0, -1, True, "17", None])
def test_delete_payment_rejects_invalid_id(payment_id):
    with patch.object(bma, "_require_role"), patch.object(bma, "db_cursor") as db_cursor:
        with pytest.raises(ValueError, match="Invalid payment_id"):
            bma.delete_payment(payment_id)

    db_cursor.assert_not_called()


def test_delete_payment_rejects_missing_payment():
    cursor = MagicMock()
    cursor.fetchone.return_value = None

    with patch.object(bma, "_require_role"), patch.object(
        bma, "db_cursor"
    ) as db_cursor:
        db_cursor.return_value.__enter__.return_value = cursor

        with pytest.raises(ValueError, match="Payment #17 not found"):
            bma.delete_payment(17)

    assert cursor.execute.call_count == 1


def test_delete_payment_rejects_unauthorized_user():
    with patch.object(
        bma, "_require_role", side_effect=Exception("You do not have permission")
    ), patch.object(bma, "db_cursor") as db_cursor:
        with pytest.raises(Exception, match="You do not have permission"):
            bma.delete_payment(17)

    db_cursor.assert_not_called()


def test_get_payments_details_includes_payment_id():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        (datetime.date(2026, 1, 1), "JC-1", "Cash", 100, 40, 0, 60, 17)
    ]

    with patch.object(bma, "_get_current_user"), patch.object(
        bma, "db_cursor"
    ) as db_cursor:
        db_cursor.return_value.__enter__.return_value = cursor

        result = bma.getPaymentsDetails(42)

    assert result[0]["PaymentID"] == 17
