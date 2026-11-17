from ._common import *

# *************************************************** Import Order Tracking Section ************************************
@anvil.server.callable()
def saveImportOrderTracking(
    dateValue, clientID, partname, partnumber, quantity, brand, status
):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_importordertracking
                (OrderDate, ClientID, PartName, PartNumber, Quantity, Brand, Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query, (dateValue, clientID, partname, partnumber, quantity, brand, status)
        )
    return "Import order tracking saved successfully"


@anvil.server.callable()
def search_client_import_orders(search_text: str):
    """
    Search client contacts by name or phone.
    Return unique (Fullname - OrderDate) options for dropdown,
    storing {"client_id": ..., "order_date": ...} as the value.
    """
    _get_current_user()
    with db_cursor() as cursor:
        sql = """
            SELECT DISTINCT
                   tbl_clientcontacts.ID AS ClientID,
                   tbl_clientcontacts.Fullname,
                   tbl_importordertracking.OrderDate
            FROM tbl_clientcontacts
            INNER JOIN tbl_importordertracking
              ON tbl_clientcontacts.ID = tbl_importordertracking.ClientID
            WHERE tbl_clientcontacts.Fullname LIKE %s
               OR tbl_clientcontacts.Phone LIKE %s
            ORDER BY tbl_importordertracking.OrderDate DESC
        """
        like_pattern = f"%{search_text}%"
        cursor.execute(sql, (like_pattern, like_pattern))
        rows = cursor.fetchall()

        results = [
            (f"{row[1]} - {row[2]}", {"client_id": row[0], "order_date": row[2]})
            for row in rows
        ]
        return results


@anvil.server.callable()
def get_import_orders_for_selection(client_id: int = None, order_date: str = None):
    """
    Return import order rows.

    If client_id and order_date are provided:
        Return matching records only.

    If no parameters are provided:
        Return all records.
    """

    _get_current_user()

    with db_cursor() as cursor:

        base_sql = """
            SELECT 
                   tbl_importordertracking.PartName AS Name,
                   tbl_importordertracking.PartNumber AS Part_No,
                   tbl_importordertracking.Quantity,
                   tbl_importordertracking.Brand,
                   tbl_importordertracking.Status,
                   tbl_importordertracking.OrderDate,
                   tbl_clientcontacts.Fullname
            FROM tbl_importordertracking
            INNER JOIN tbl_clientcontacts
              ON tbl_clientcontacts.ID = tbl_importordertracking.ClientID
        """

        params = []
        conditions = []

        # Add conditions dynamically
        if client_id is not None:
            conditions.append("tbl_importordertracking.ClientID = %s")
            params.append(client_id)

        if order_date is not None:
            conditions.append("tbl_importordertracking.OrderDate = %s")
            params.append(order_date)

        # Append WHERE clause if conditions exist
        if conditions:
            base_sql += " WHERE " + " AND ".join(conditions)

        # Final ordering
        base_sql += " ORDER BY tbl_importordertracking.ID"

        cursor.execute(base_sql, tuple(params))

        rows = cursor.fetchall()

        # Convert rows to list of dicts
        results = [
            {
                "No": idx + 1,
                "Name": r[0],
                "Part_No": r[1],
                "Quantity": r[2],
                "Brand": r[3],
                "Status": r[4],
                "OrderDate": r[5],
                "Client": r[6],
            }
            for idx, r in enumerate(rows)
        ]

        return results

@anvil.server.callable()
def updateImportOrderTracking(dateID, clientId, items):
    _get_current_user()
    with db_cursor() as cursor:
        # Delete existing records for the client and date
        cursor.execute(
            "DELETE FROM tbl_importordertracking WHERE ClientID = %s AND OrderDate = %s",
            (clientId, dateID),
        )

        # Append new records
        for item in items:
            query = """
                INSERT INTO tbl_importordertracking
                (OrderDate, ClientID, PartName, PartNumber, Quantity, Brand, Status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    dateID,
                    clientId,
                    item["name"],
                    item["number"],
                    item["quantity"],
                    item["brand"],
                    item["status"],
                ),
            )
    return "Import order tracking updated successfully"


# *************************************************** Monthly Performance Schedule Section ************************************


@anvil.server.callable()
def getMonthlyJobcardRef(startDate, endDate):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT tbl_jobcarddetails.JobCardRef,
                   tbl_invoices.Date, tbl_invoices.AssignedJobID
            FROM tbl_jobcarddetails
            INNER JOIN tbl_invoices
              ON tbl_jobcarddetails.ID = tbl_invoices.AssignedJobID
            WHERE tbl_invoices.Date BETWEEN %s AND %s
            GROUP BY tbl_jobcarddetails.JobCardRef, tbl_invoices.Date, tbl_invoices.AssignedJobID
            ORDER BY tbl_invoices.Date DESC
        """
        cursor.execute(query, (startDate, endDate))
        rows = cursor.fetchall()

        # Return list of tuples (label, value)
        return [(f"{r[0]} - {r[1].strftime('%Y-%m-%d')}", r[2]) for r in rows]


@anvil.server.callable()
def getPeriodicInvoices(startDate, endDate, jobcardref):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                tbl_invoices.Date, 
                tbl_invoices.Item, 
                tbl_invoices.Part_No, 
                tbl_invoices.QuantityIssued,
                tbl_invoices.Amount
            FROM tbl_invoices
            WHERE tbl_invoices.Date BETWEEN %s AND %s 
              AND tbl_invoices.AssignedJobID = %s
            ORDER BY tbl_invoices.Date DESC
        """
        cursor.execute(query, (startDate, endDate, jobcardref))
        rows = cursor.fetchall()

        # Add row number with enumerate
        result = [
            {
                "No": idx,  # row number
                "Date": r[0].strftime("%Y-%m-%d") if r[0] else None,
                "Item": r[1],
                "Part_No": r[2],
                "QuantityIssued": r[3],
                "Amount": f"{float(r[4]):,.2f}" if r[4] is not None else "0.00",
            }
            for idx, r in enumerate(rows, start=1)
        ]

        return result


@anvil.server.callable()
def getFullnameInvoiceAmountAndBalance(jobcard_id):
    # --- Get invoice details ---
    _get_current_user()
    invoice_rows = get_invoice_details_by_job_id(jobcard_id)
    if not invoice_rows:
        return {
            "Fullname": "",
            "TotalInvoiceAmount": 0.0,
            "TotalAmountPaid": 0.0,
            "TotalDiscount": 0.0,
            "MaxBalance": 0.0,
        }

    # Get the client fullname from the first row
    fullname = invoice_rows[0].get("Fullname", "")

    # Calculate the total invoice amount (sum of all item totals)
    total_invoice = sum(float(row.get("Total") or 0) for row in invoice_rows)

    # --- Get payment details ---
    payment_rows = getPaymentsDetails(jobcard_id)

    def safe_to_float(value):
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", ""))
            except ValueError:
                return 0.0
        return 0.0

    total_amount_paid = sum(
        safe_to_float(row.get("AmountPaid")) for row in payment_rows
    )

    total_discount = sum(safe_to_float(row.get("Discount")) for row in payment_rows)

    # Calculate balance
    balance = total_invoice - total_amount_paid - total_discount

    # Return formatted dictionary
    return {
        "Fullname": fullname,
        "TotalInvoiceAmount": round(total_invoice, 2),
        "TotalAmountPaid": round(total_amount_paid, 2),
        "TotalDiscount": round(total_discount, 2),
        "Balance": round(balance, 2),
    }


@anvil.server.callable()
def deleteMonthlySchedule(jobcardrefID):
    _get_current_user()
    with db_cursor() as cursor:
        cursor.execute(
            "DELETE FROM tbl_monthlyschedule WHERE AssignedJobID = %s", (jobcardrefID,)
        )
    return "Monthly schedule deleted successfully"


@anvil.server.callable()
def saveMonthlySchedule(
    invoiceDate,
    jobcardrefID,
    fullname,
    invoiceTotal,
    totalPaid,
    totalDiscount,
    balance,
    item,
    partNo,
    quantity,
    amount,
    category,
):
    _get_current_user()
    """
    Inserts a record into tbl_monthlyschedule table.
    Called for each row from the client repeating panel.
    """

    # Helper function to safely convert strings to float
    def safe_float(value):
        if value is None or value == "":
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        # Remove commas and whitespace before conversion
        return float(str(value).replace(",", "").strip())

    with db_cursor() as cursor:
        # Insert new record
        query = """
            INSERT INTO tbl_monthlyschedule
            (Date, AssignedJobID, ClientName, TotalInvoiceAmount,
             TotalAmountPaid, TotalDiscount, PaymentBalance, 
             Item, Part_No, QuantityIssued, Amount, Category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            invoiceDate,
            int(jobcardrefID),
            fullname,
            safe_float(invoiceTotal),
            safe_float(totalPaid),
            safe_float(totalDiscount),
            safe_float(balance),
            item,
            partNo,
            safe_float(quantity) if quantity is not None else None,
            safe_float(amount),
            category,
        )

        cursor.execute(query, values)
    return "Monthly schedule saved successfully"


# *************************************************** Monthly Schedule Pivot Section ************************************
@anvil.server.callable()
def get_monthly_schedule_pivot(start_date=None, end_date=None):
    """
    Returns a pivoted summary of monthly schedule data between start_date and end_date.
    Each category becomes its own column, with totals based on QuantityIssued * Amount if QuantityIssued is not NULL.
    Computes Balance = PaymentBalance + PrevBal safely after SQL aggregation.
    """
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                tbl_monthlyschedule.Date,
                tbl_monthlyschedule.AssignedJobID,
                tbl_monthlyschedule.ClientName,
                tbl_monthlyschedule.TotalInvoiceAmount,
                tbl_monthlyschedule.TotalAmountPaid,
                tbl_monthlyschedule.TotalDiscount,
                tbl_monthlyschedule.PaymentBalance,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Car Parts'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS CarParts,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Engine Oil'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS EngineOil,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Consumable'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS Consumable,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Diagnosis'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS Diagnosis,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Labour'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS Labour,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Engine Wash'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS EngineWash,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Alignment'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS Alignment,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Transfer / Gearbox Oil'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS TransferGearboxOil,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Others'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS Others,

                SUM(CASE WHEN tbl_monthlyschedule.Category = 'Prev Bal'
                         THEN IF(tbl_monthlyschedule.QuantityIssued IS NOT NULL,
                                 tbl_monthlyschedule.QuantityIssued * tbl_monthlyschedule.Amount,
                                 tbl_monthlyschedule.Amount)
                    ELSE 0 END) AS PrevBal

            FROM tbl_monthlyschedule
            WHERE (%s IS NULL OR tbl_monthlyschedule.Date >= %s)
              AND (%s IS NULL OR tbl_monthlyschedule.Date <= %s)
            GROUP BY 
                tbl_monthlyschedule.Date,
                tbl_monthlyschedule.AssignedJobID,
                tbl_monthlyschedule.ClientName,
                tbl_monthlyschedule.TotalInvoiceAmount,
                tbl_monthlyschedule.TotalAmountPaid,
                tbl_monthlyschedule.TotalDiscount,
                tbl_monthlyschedule.PaymentBalance
            ORDER BY tbl_monthlyschedule.Date DESC;
        """

        cursor.execute(query, (start_date, start_date, end_date, end_date))
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        results = [dict(zip(column_names, row)) for row in rows]

        # Compute Balance = PaymentBalance + PrevBal safely in Python
        for r in results:
            payment_balance = r.get("PaymentBalance") or 0
            #prev_bal = r.get("PrevBal") or 0
            r["Balance"] = round(payment_balance, 2)

        return results

__all__ = [
    'saveImportOrderTracking',
    'search_client_import_orders',
    'get_import_orders_for_selection',
    'updateImportOrderTracking',
    'getMonthlyJobcardRef',
    'getPeriodicInvoices',
    'getFullnameInvoiceAmountAndBalance',
    'deleteMonthlySchedule',
    'saveMonthlySchedule',
    'get_monthly_schedule_pivot',
]

from . import BMALocal as _compatibility_facade
