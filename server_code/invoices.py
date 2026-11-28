from ._common import *

# ***************************************************Invoice Details Section ************************************
@anvil.server.callable()
def getInvoiceJobCardDetails():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT DISTINCT tbl_jobcarddetails.JobCardRef, tbl_invoices.AssignedJobID
            FROM tbl_invoices 
            INNER JOIN tbl_jobcarddetails 
            ON tbl_invoices.AssignedJobID = tbl_jobcarddetails.ID
            ORDER BY tbl_jobcarddetails.JobCardRef;
        """

        cursor.execute(query)
        result = cursor.fetchall()
        return [{"JobCardRef": r[0], "ID": r[1]} for r in result]


@anvil.server.callable()
def saveInvoice(assignedDate, jobCardID, items):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_invoices 
            (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount, Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for item in items:
            cursor.execute(
                query,
                (
                    assignedDate,
                    jobCardID,
                    item["name"],
                    item["number"],
                    item["quantity"],
                    item["amount"],
                    "Pending",
                ),
            )
        query2 = """
            INSERT INTO tbl_assignedcarparts ( Date, AssignedJobID, CarPartID, QuantityIssued )
            VALUES (%s, %s, %s, %s)
        """
        for item2 in items:
            if item2["CarPartID"] is not None:
                cursor.execute(
                    query2,
                    (assignedDate, jobCardID, item2["CarPartID"], item2["quantity"]),
                )
    publish_realtime_event("payments", "invoice_saved", entity_id=jobCardID)
    publish_realtime_event("jobcards", "invoice_saved", entity_id=jobCardID)
    publish_realtime_event("inventory", "parts_issued", entity_id=jobCardID)


def _safe_invoice_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float, decimal.Decimal)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return None


def _fetch_invoice_details_by_job_id(cursor, job_id):
    query = """
            SELECT 
                tbl_clientcontacts.Fullname, 
                tbl_jobcarddetails.MakeAndModel, 
                tbl_jobcarddetails.RegNo, 
                tbl_invoices.Date, 
                tbl_jobcarddetails.ChassisNo, 
                tbl_jobcarddetails.EngineCode, 
                tbl_jobcarddetails.Mileage, 
                tbl_invoices.Item, 
                tbl_invoices.QuantityIssued, 
                tbl_invoices.Amount, 
                tbl_invoices.AssignedJobID,
                tbl_invoices.Part_No,
                tbl_carpartnames.ID AS CarPartID,
                tbl_invoices.Status
            FROM 
                (tbl_jobcarddetails 
                INNER JOIN tbl_clientcontacts 
                    ON tbl_jobcarddetails.ClientDetails = tbl_clientcontacts.ID) 
            INNER JOIN tbl_invoices 
                ON tbl_jobcarddetails.ID = tbl_invoices.AssignedJobID
            LEFT JOIN tbl_carpartnames
                ON tbl_invoices.Part_No = tbl_carpartnames.PartNo
            WHERE 
                tbl_invoices.AssignedJobID = %s
            ORDER BY 
                tbl_invoices.ID
    """
    cursor.execute(query, (job_id,))
    rows = cursor.fetchall()

    result = []
    for r in rows:
        quantity_issued_val = _safe_invoice_float(r[8])
        amount_val = _safe_invoice_float(r[9])
        display_quantity_issued = (
            ""
            if r[8] is None or not isinstance(r[8], (int, float, decimal.Decimal))
            else quantity_issued_val
        )
        total_calc = None
        if quantity_issued_val is None:
            total_calc = amount_val
        elif amount_val is not None:
            total_calc = round(quantity_issued_val * amount_val, 2)

        row_dict = {
            "Fullname": r[0],
            "MakeAndModel": r[1],
            "RegNo": r[2],
            "Date": r[3],
            "ChassisNo": r[4],
            "EngineCode": r[5],
            "Mileage": r[6],
            "Item": r[7],
            "QuantityIssued": display_quantity_issued,
            "Amount": amount_val,
            "AssignedJobID": r[10],
            "PartNo": r[11],
            "CarPartID": r[12],
            "Total": total_calc,
        }
        if len(r) > 13:
            row_dict["Status"] = r[13]
        result.append(row_dict)
    return result


@anvil.server.callable()
def get_invoice_details_by_job_id(job_id):
    _get_current_user()
    with db_cursor() as cursor:
        return _fetch_invoice_details_by_job_id(cursor, job_id)



@anvil.server.callable()
def getJobcardEitherInQuotesOrPendingInvoices(jobcardref):
    _get_current_user()

    with db_cursor() as cursor:
        query = """
            SELECT
                tbl_invoices.AssignedJobID,
                tbl_jobcarddetails.JobCardRef
            FROM tbl_invoices
            INNER JOIN tbl_jobcarddetails
                ON tbl_invoices.AssignedJobID = tbl_jobcarddetails.ID
            WHERE tbl_invoices.Status = 'Pending'
            And tbl_jobcarddetails.JobCardRef = %s
            GROUP BY
                tbl_invoices.AssignedJobID,
                tbl_jobcarddetails.JobCardRef
        """

        cursor.execute(query, (jobcardref,))
        result = cursor.fetchall()
        source="Invoice"
        
        if not result:
            query2 = """
                SELECT
                    tbl_quotation.AssignedJobID,
                    tbl_jobcarddetails.JobCardRef
                FROM tbl_quotation
                INNER JOIN tbl_jobcarddetails
                    ON tbl_quotation.AssignedJobID = tbl_jobcarddetails.ID
                WHERE tbl_jobcarddetails.JobCardRef = %s
                GROUP BY
                    tbl_quotation.AssignedJobID,
                    tbl_jobcarddetails.JobCardRef
            """

            cursor.execute(query2, (jobcardref,))
            result = cursor.fetchall()
            source = "Quotation"
        return [
            {"ID": r[0], "JobCardRef": r[1], "Source": source}
            for r in result
        ]



@anvil.server.callable()
def get_invoice_total_by_job_id(assigned_job_id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT SUM(
                COALESCE(QuantityIssued, 1) * Amount
            ) AS GrandTotal
            FROM tbl_invoices
            WHERE AssignedJobID = %s
        """
        cursor.execute(query, (assigned_job_id,))
        result = cursor.fetchone()
        return f"{float(result[0]):,.2f}" if result and result[0] is not None else 0.0


@anvil.server.callable()
def update_invoice_status(jobCardRefID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_invoices
            SET Status = 'Paid'
            WHERE AssignedJobID = %s
        """
        cursor.execute(query, (jobCardRefID,))
    publish_realtime_event("payments", "invoice_paid", entity_id=jobCardRefID)
    publish_realtime_event("jobcards", "invoice_paid", entity_id=jobCardRefID)


@anvil.server.callable()
def get_invoice_totals_and_counts_by_date(start_date, end_date):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Status,
                   COUNT(DISTINCT AssignedJobID) AS count,
                   SUM(
                       CASE
                           WHEN QuantityIssued IS NULL THEN 1 * Amount
                           ELSE QuantityIssued * Amount
                       END
                   ) AS total
            FROM tbl_invoices
            WHERE Status IN ('Pending', 'Paid')
              AND Date BETWEEN %s AND %s
            GROUP BY Status
        """
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()

        # Structure: { "Pending": {"count": X, "total": Y}, "Paid": {...} }
        summary = {
            "Pending": {"count": 0, "total": 0.0},
            "Paid": {"count": 0, "total": 0.0},
        }

        for status, count, total in results:
            summary[status]["count"] = count
            summary[status]["total"] = float(total) if total else 0.0

        return summary


@anvil.server.callable()
def getJobCardRefInvoiceDetails(value):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT DISTINCT 
                tbl_jobcarddetails.ID, tbl_jobcarddetails.JobCardRef 
            FROM 
                tbl_jobcarddetails 
            JOIN 
                tbl_invoices ON tbl_jobcarddetails.ID = tbl_invoices.AssignedJobID 
            WHERE 
                tbl_invoices.Status = 'Pending' 
            AND 
                tbl_jobcarddetails.JobCardRef LIKE %s
            ORDER BY 
                tbl_jobcarddetails.JobCardRef DESC;
        """

        like_value = f"%{value}%"
        cursor.execute(query, (like_value,))
        result = cursor.fetchall()

        # Return directly as list of tuples for a dropdown [(display_text, value), ...]
        return [(row[1], row[0]) for row in result]  # (JobCardRef, AssignedJobID)


@anvil.server.callable()
def updateInvoice(invoicedate, job_card_id, items):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            DELETE FROM tbl_invoices WHERE AssignedJobID = %s
        """
        cursor.execute(query, (job_card_id,))

        query2 = """
            INSERT INTO tbl_invoices (Date,AssignedJobID, Item, Part_No, QuantityIssued, Amount, Status)
            VALUES (%s, %s, %s, %s, %s, %s, "Pending")
        """

        for item in items:
            cursor.execute(
                query2,
                (
                    invoicedate,
                    job_card_id,
                    item.get("name"),
                    item.get("number"),
                    item.get("quantity"),
                    item.get("amount"),
                ),
            )
        query3 = """
            DELETE FROM tbl_assignedcarparts WHERE AssignedJobID = %s
        """
        cursor.execute(query3, (job_card_id,))

        query4 = """
            INSERT INTO tbl_assignedcarparts ( Date, AssignedJobID, CarPartID, QuantityIssued )
            VALUES (%s, %s, %s, %s)
        """
        for item2 in items:
            if item2["CarPartID"] is not None:
                cursor.execute(
                    query4,
                    (invoicedate, job_card_id, item2["CarPartID"], item2["quantity"]),
                )
    publish_realtime_event("payments", "invoice_updated", entity_id=job_card_id)
    publish_realtime_event("jobcards", "invoice_updated", entity_id=job_card_id)
    publish_realtime_event("inventory", "parts_issued", entity_id=job_card_id)


@anvil.server.callable()
def getInvoiceStatus(jobcardID):
    _get_current_user()
    with db_cursor() as cursor:
        query = "SELECT DISTINCT Status FROM tbl_invoices WHERE AssignedJobID = %s"
        cursor.execute(query, (jobcardID,))
        result = cursor.fetchone()
        return result[0] if result else None


# ***************************************************Payment Details Section ************************************


@anvil.server.callable()
def get_previous_payment(jobcardrefid):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT SUM(AmountPaid)
            FROM tbl_payments
            WHERE JobCardRefID = %s
        """
        cursor.execute(query, (jobcardrefid,))
        result = cursor.fetchone()
        return f"{float(result[0]):,.2f}" if result[0] is not None else 0.0

@anvil.server.callable()
def get_discount_payment(jobcardrefid):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT SUM(Discount)
            FROM tbl_payments
            WHERE JobCardRefID = %s
        """
        cursor.execute(query, (jobcardrefid,))
        result = cursor.fetchone()
        return f"{float(result[0]):,.2f}" if result[0] is not None else 0.0
    
@anvil.server.callable()
def save_payment_details(
    paymentDate, jobCardRefID, paymentMode, amountPaid, discount, bal
):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_payments (Date, JobCardRefID, PaymentMode, AmountPaid, Discount, Balance)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query, (paymentDate, jobCardRefID, paymentMode, amountPaid, discount, bal)
        )
    publish_realtime_event("payments", "payment_created", entity_id=jobCardRefID)
    publish_realtime_event("jobcards", "payment_created", entity_id=jobCardRefID)



@anvil.server.callable()
def getPaidPendingInvoices(status, start_date, end_date):
    _get_current_user()
    count = 0
    with db_cursor() as cursor:
        query = """
        SELECT tbl_invoices.Date,  tbl_jobcarddetails.JobCardRef,  tbl_invoices.Item,  tbl_invoices.Part_No, tbl_invoices.QuantityIssued, tbl_invoices.Amount
        FROM tbl_invoices 
        JOIN tbl_jobcarddetails ON tbl_invoices.AssignedJobID = tbl_jobcarddetails.ID 
        WHERE tbl_invoices.STATUS = %s AND tbl_invoices.DATE BETWEEN %s AND %s 
        ORDER BY tbl_invoices.DATE DESC;
        """
        # Pass all parameters to the execute method in the correct order
        cursor.execute(query, (status, start_date, end_date))
        rows = cursor.fetchall()
        result = []
        for count, row in enumerate(rows, start=1):
            # Helper function to ensure we get a float from various types
            def safe_float_convert(value):
                if value is None:
                    return None  # Or 0.0, depending on desired behavior for NULLs
                if isinstance(value, (int, float, decimal.Decimal)):
                    return float(value)
                # If it's a string, try to clean it and convert
                if isinstance(value, str):
                    try:
                        return float(value.replace(",", ""))
                    except ValueError:
                        # Handle cases where string cannot be converted (e.g., non-numeric string)
                        print(f"Warning: Could not convert string '{value}' to float.")
                        return None  # Or raise an error
                return None  # Default if type is unexpected

            quantity_issued_val = safe_float_convert(row[4])  # QuantityIssued
            amount_val = safe_float_convert(row[5])  # Amount

            # Ensure 'QuantityIssued' for the dictionary can be "" if originally None or non-numeric string
            # If your front-end expects an empty string, keep this logic
            display_quantity_issued = (
                ""
                if row[4] is None
                or not isinstance(row[4], (int, float, decimal.Decimal))
                else quantity_issued_val
            )

            # Calculate Total - ensuring we use the float versions for calculation
            total_calc = None
            if quantity_issued_val is None:  # If QuantityIssued was NULL/None from DB
                total_calc = amount_val
            elif amount_val is not None:  # Ensure Amount is not None for multiplication
                total_calc = round(quantity_issued_val * amount_val, 2)
            # If amount_val is None and quantity_issued_val is not None, total_calc would remain None

            result.append(
                {
                    "No": count,
                    "Date": row[0],
                    "JobCardRef": row[1],
                    "Item": row[2],
                    "PartNo": row[3],
                    "Quantity": display_quantity_issued,
                    "Amount": f"{float(amount_val):,.2f}",
                    "Total": f"{float(total_calc):,.2f}",
                }
            )

        return result



def _fetch_payments_details(cursor, paymentID):
    # 1. Check invoices first
    query = """
        SELECT
            p.Date,
            j.JobCardRef,
            p.PaymentMode,
            SUM(
                COALESCE(i.QuantityIssued, 1) * i.Amount
            ) AS InvoiceAmount,
            p.AmountPaid,
            p.Discount,
            p.Balance,
            p.ID
        FROM tbl_payments AS p
        JOIN tbl_jobcarddetails AS j
            ON p.JobCardRefID = j.ID
        JOIN tbl_invoices AS i
            ON j.ID = i.AssignedJobID
        WHERE p.JobCardRefID = %s
        GROUP BY
            p.ID,
            p.Date,
            j.JobCardRef,
            p.PaymentMode,
            p.AmountPaid,
            p.Discount,
            p.Balance
        ORDER BY p.Date ASC
    """
    cursor.execute(query, (paymentID,))
    rows = cursor.fetchall()
    source = "Invoice"

    # 2. If no invoice records exist, check quotations
    if not rows:
        query2 = """
            SELECT
                p.Date,
                j.JobCardRef,
                p.PaymentMode,
                SUM(
                    COALESCE(q.QuantityIssued, 1) * q.Amount
                ) AS QuotationAmount,
                p.AmountPaid,
                p.Discount,
                p.Balance,
                p.ID
            FROM tbl_payments AS p
            JOIN tbl_jobcarddetails AS j
                ON p.JobCardRefID = j.ID
            JOIN tbl_quotation AS q
                ON j.ID = q.AssignedJobID
            WHERE p.JobCardRefID = %s
            GROUP BY
                p.ID,
                p.Date,
                j.JobCardRef,
                p.PaymentMode,
                p.AmountPaid,
                p.Discount,
                p.Balance
            ORDER BY p.Date ASC
        """
        cursor.execute(query2, (paymentID,))
        rows = cursor.fetchall()
        source = "Quotation"

    return [
        {
            "No": index + 1,
            "Date": row[0].strftime("%d-%m-%Y") if row[0] else None,
            "JobCardRef": row[1],
            "PaymentMode": row[2],
            "ChargedAmount": f"{float(row[3]):,.2f}" if row[3] is not None else "0.00",
            "AmountPaid": f"{float(row[4]):,.2f}" if row[4] is not None else "0.00",
            "Discount": f"{float(row[5]):,.2f}" if row[5] is not None else "0.00",
            "Balance": f"{float(row[6]):,.2f}" if row[6] is not None else "0.00",
            "PaymentID": row[7],
            "Source": source,
        }
        for index, row in enumerate(rows)
    ]


@anvil.server.callable()
def getPaymentsDetails(paymentID):
    _get_current_user()
    with db_cursor() as cursor:
        return _fetch_payments_details(cursor, paymentID)

@anvil.server.callable()
def delete_payment(payment_id):
    if type(payment_id) is not int or payment_id <= 0:
        raise ValueError("Invalid payment_id provided.")

    with db_cursor() as cursor:
        cursor.execute(
            "SELECT JobCardRefID FROM tbl_payments WHERE ID = %s FOR UPDATE",
            (payment_id,),
        )
        payment = cursor.fetchone()
        if payment is None:
            raise ValueError(f"Payment #{payment_id} not found.")

        jobcard_id = payment[0]
        cursor.execute("DELETE FROM tbl_payments WHERE ID = %s", (payment_id,))

        cursor.execute(
            """
            SELECT SUM(COALESCE(QuantityIssued, 1) * Amount)
            FROM tbl_invoices
            WHERE AssignedJobID = %s
            """,
            (jobcard_id,),
        )
        invoice_total_row = cursor.fetchone()
        invoice_total = (
            float(f"{invoice_total_row[0]:.2f}")
            if invoice_total_row and invoice_total_row[0] is not None
            else None
        )

        if invoice_total is None:
            cursor.execute(
                """
                SELECT SUM(COALESCE(QuantityIssued, 1) * Amount)
                FROM tbl_quotation
                WHERE AssignedJobID = %s
                """,
                (jobcard_id,),
            )
            quotation_total_row = cursor.fetchone()
            balance_total = (
                float(f"{quotation_total_row[0]:.2f}")
                if quotation_total_row and quotation_total_row[0] is not None
                else None
            )
        else:
            balance_total = invoice_total

        total_paid = 0.0
        balance_updates = []
        if balance_total is not None:
            cursor.execute(
                """
                SELECT ID, AmountPaid, Discount
                FROM tbl_payments
                WHERE JobCardRefID = %s
                ORDER BY Date ASC, ID ASC
                """,
                (jobcard_id,),
            )
        for remaining_id, amount_paid, discount in cursor.fetchall():
            total_paid = float(
                f"{total_paid + float(amount_paid or 0) + float(discount or 0):.2f}"
                )
            balance_updates.append(
                (float(f"{balance_total - total_paid:.2f}"), remaining_id)
                )
        
        if balance_updates:
            cursor.executemany(
                "UPDATE tbl_payments SET Balance = %s WHERE ID = %s", balance_updates,
                )
                             
        if invoice_total is not None:
            cursor.execute(
                """
                UPDATE tbl_invoices
                SET Status = CASE
                    WHEN %s >= %s THEN 'Paid'
                    WHEN Status = 'Paid' THEN 'Pending'
                    ELSE Status
                END
                WHERE AssignedJobID = %s
                """,
                (total_paid, invoice_total, jobcard_id),
            )

    publish_realtime_event("payments", "payment_deleted", entity_id=jobcard_id)
    publish_realtime_event("jobcards", "payment_deleted", entity_id=jobcard_id)
    return {"success": True, "payment_id": payment_id, "jobcard_id": jobcard_id}


@anvil.server.callable()
def get_payment_ref():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT
              DISTINCT j.JobCardRef,
              p.JobCardRefID
            FROM
              tbl_payments AS p
            JOIN
              tbl_jobcarddetails AS j ON p.JobCardRefID = j.ID
            ORDER BY
              j.JobCardRef ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        result = [{"JobCardRef": row[0], "JobCardRefID": row[1]} for row in rows]

        return result


@anvil.server.callable()
def fillReportData(jobCardID, docType, logo_path: str = os.getenv("LOGO"), font_path: str = os.getenv("FONT_PATH")) -> str:
    _get_current_user()
    if docType == "Payment":
        docTitle = "Payment Details"
        reportdetails = getPaymentsDetails(jobCardID)
        vehicledetails = get_invoice_details_by_job_id(jobCardID)
        if not vehicledetails: # jobCardID does not exist in tbl_invoices but exits in tbl_quotation
            vehicledetails = get_quote_details_by_job_id(jobCardID)

    # === Embed MozillaHeadline font as base64 ===
    font_base64 = ""
    if font_path and os.path.exists(font_path):
        with open(font_path, "rb") as f:
            font_base64 = base64.b64encode(f.read()).decode("utf-8")

    # === Handle company logo ===
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as logo_file:
            logo_base64 = base64.b64encode(logo_file.read()).decode("utf-8")
        logo_img_tag = f'<img src="data:image/png;base64,{logo_base64}" alt="Company Logo" style="width: 100%; height: 100%; border-radius: 2px;">'
    else:
        logo_img_tag = "LOGO"

    # Generate items table rows
    items_html = ""
    counter = 0
    seen_refs = set()
    for item in reportdetails:
        counter += 1
        ref = item['JobCardRef']
        if ref in seen_refs:
            invoice_display = ""
        else:
            invoice_display = html_module.escape(str(item['ChargedAmount']))
            seen_refs.add(ref)

        items_html += f"""
                    <tr class="item-row">
                        <td>{counter}</td>
                        <td>{html_module.escape(str(item['Date']))}</td>
                        <td>{html_module.escape(str(ref))}</td>
                        <td>{html_module.escape(str(item['PaymentMode']))}</td>
                        <td>{invoice_display}</td>
                        <td>{html_module.escape(str(item['AmountPaid']))}</td>
                        <td>{html_module.escape(str(item['Discount']))}</td>
                        <td>{html_module.escape(str(item['Balance']))}</td>
                    </tr>"""

        # Complete HTML template with fixed structure
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{docTitle}</title>
    <style>
        /* --- Embed Mozilla Headline font --- */
        @font-face {{
            font-family: 'Mozilla Headline';
            src: url(data:font/ttf;base64,{font_base64}) format('truetype');
        }}
        body {{
            font-family: Roboto, Noto, Arial, sans-serif;
            font-size: 14px;
            line-height: 1.4286;
            background-color: #fafafa;
            margin: 0;
            padding: 16px;
        }}

        .quotation-container {{
            background-color: white;
            border-radius: 2px;
            box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.14),
                        0 3px 1px -2px rgba(0, 0, 0, 0.2),
                        0 1px 5px 0 rgba(0, 0, 0, 0.12);
            max-width: 800px;
            margin: 0 auto;
            overflow: hidden;
        }}

        .logo-section {{
            text-align: center;
            padding: 24px;
            background-color: white;
            border-bottom: 1px solid #e0e0e0;
        }}

        .logo-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 16px;
        }}

        .logo-image {{
            width: 725px;
            height: 100px;
            background: linear-gradient(135deg, #228B22, #90EE90, #FFD700, #FF6347);
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
            font-weight: 500;
            box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.14),
                        0 3px 1px -2px rgba(0, 0, 0, 0.2),
                        0 1px 5px 0 rgba(0, 0, 0, 0.12);
        }}

        .header {{
            background-color: #000;
            color: white;
            text-align: center;
            padding: 16px 24px;
            font-size: 16px;
            font-weight: 300;
            letter-spacing: .5px;
            box-shadow: 0 4px 5px 0 rgba(0, 0, 0, 0.14),
                        0 1px 10px 0 rgba(0, 0, 0, 0.12),
                        0 2px 4px -1px rgba(0, 0, 0, 0.2);
        }}

        .detail-row {{
            display: grid;
            grid-template-columns: 140px 1fr; /* label column, value column */
            column-gap: 8px;
            margin-bottom: 12px;
        }}

        .detail-label {{
                font-weight: bold;
                font-size: 16px;
                color: rgba(0,0,0,0.87);
                
        }}

        .detail-value {{
            font-size: 16px;
            color: rgba(0,0,0,0.87);
            text-align: left;
            
        }}

        .items-table {{
            border-collapse: collapse;
            width: 100%;
            margin: 0 24px 24px 0;
            background-color: white;
            border-radius: 2px;
            overflow: hidden;
            box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.14),
                        0 3px 1px -2px rgba(0, 0, 0, 0.2),
                        0 1px 5px 0 rgba(0, 0, 0, 0.12);
        }}

        .items-table th {{
            background-color: #f5f5f5;
            border-bottom: 1px solid #e0e0e0;
            padding: 16px;
            text-align: left;
            font-weight: bold;
            font-size: 14px;
            color: rgba(0,0,0,0.87);
            text-transform: uppercase;
            letter-spacing: .5px;
            
        }}

        .items-table td {{
            border-bottom: 1px solid rgba(0,0,0,0.12);
            padding: 16px;
            font-size: 14px;
            color: rgba(0,0,0,0.87);
           
        }}

        .items-table .item-row:hover {{
            background-color: rgba(0,0,0,0.04);
        }}

        .total-row {{
            background-color: #000 !important;
            color: white !important;
        }}

        .total-row td {{
            border-bottom: none !important;
            font-weight: 300;
            font-size: 16px;
            color: white !important;
            padding: 16px;
           
        }}

        .notes-section {{
            padding: 24px;
            background-color: #f5f5f5;
            margin-top: 16px;
        }}

        .notes-title {{
            margin-bottom: 16px;
            font-weight: 500;
            font-size: 16px;
            color: rgba(0,0,0,0.87);
            font-family: 'Mozilla Headline';
        }}

        .notes-list {{
            margin: 0;
            padding-left: 24px;
            color: rgba(0,0,0,0.74);
        }}

        .notes-list li {{
            margin-bottom: 8px;
            line-height: 1.5;
            font-family: 'Mozilla Headline';
        }}
        #footer  div {{
                width: 80%;
                margin: 0 auto;
                text-align: center;
                font-size: 12px;
                font-family: 'Mozilla Headline';
            }}
    </style>
</head>
<body>
    <div class="quotation-container">
        <div class="logo-section">
            <div class="logo-container">
                <div class="logo-image">
                    {logo_img_tag}
                </div>
            </div>
        </div>

        <div class="header">
            {docTitle.upper()}
        </div>
         <!-- UPDATED: Replaced details-section div with table layout -->
        <table style="width: 100%; table-layout: fixed; margin: 24px 0;">
            <tr>
                <!-- Left Column -->
                <td style="width: 50%; vertical-align: top; padding-left: 24px; padding-right: 32px;">
                    <div class="detail-row">
                        <span class="detail-label">Customer Name:</span>
                        <div>
                        <span class="detail-value">{vehicledetails[0]['Fullname']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Make And Model:</span>
                        <div>
                        <span class="detail-value">{vehicledetails[0]['MakeAndModel']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Reg No:</span>
                        <div>
                        <span class="detail-value">{vehicledetails[0]['RegNo']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <div>
                        <span class="detail-value">{vehicledetails[0]['Date']}</span>
                        </div>
                    </div>
                </td>

                <!-- Right Column -->
                <td style="width: 50%; vertical-align: top; padding-left: 32px;">
                    <div class="detail-row">
                        <span class="detail-label">Chassis:</span>
                        <div>
                        <span class="detail-value">{vehicledetails[0]['ChassisNo']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Engine:</span>
                        <div>
                        <span class="detail-value">{vehicledetails[0]['EngineCode']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Mileage:</span>
                        <div>
                        <span class="detail-value">{vehicledetails[0]['Mileage']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">&nbsp;</span>
                        <span class="detail-value">&nbsp;</span>
                    </div>
                </td>
            </tr>
        </table>
        <!-- END UPDATED -->

        <table class="items-table">
            <thead>
                <tr>
                    <th>No.</th>
                    <th>Date</th>
                    <th>Ref</th>
                    <th>Mode</th>
                    <th>Charged</th>
                    <th>Paid</th>
                    <th>Discount</th>
                    <th>Balance</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        <footer id="footer">
        <div> 
            <p>Joy Is The Feeling Of Being Looked After By The Best - BMW CENTER For Your BMW.</p>
        </div>
    </footer>    
    </div>
    </body>
    </html>"""

    return html_content


@anvil.server.callable()
def createReportPdf(jobCardID, docType):
    _get_current_user()
    try:
        docName = getQuotationInvoiceName(jobCardID)
        if docType == "Payment":
            fileName = str(docName) + " Payment"

        setting_options = {
            "encoding": "UTF-8",
            "custom-header": [("Accept-Encoding", "gzip")],
            "page-size": "A4",
            "orientation": "Portrait",
            "margin-top": "0.75in",
            "margin-right": "0.75in",
            "margin-bottom": "0.75in",
            "margin-left": "0.75in",
            "no-outline": False,
            "enable-local-file-access": None,
        }

        html_string = fillReportData(jobCardID, docType)
        get_pdfkit().from_string(
            html_string, fileName, options=setting_options, configuration=get_pdfkit_config()
        )
        media_object = anvil.media.from_file(fileName, "application/pdf", name=fileName)
        return media_object

    except Exception as e:
        print("PDF generation failed:", str(e))
        raise


# *************************************************** Periodic Quotation And Invoice Totals Section ************************************


@anvil.server.callable()
def get_jobcard_quote_invoice_totals(jobcard_ref=None, start_date=None, end_date=None):
    """
    Returns jobcards with BOTH quotations and invoices,
    filtered by JobCardRef (LIKE) and ReceivedDate range.

    Parameters:
        jobcard_ref (str)   -> optional, partial match on JobCardRef
        start_date (date)   -> optional, filter from this date (inclusive)
        end_date (date)     -> optional, filter up to this date (inclusive)
    """
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT
                j.ID              AS ID,
                j.ReceivedDate    AS ReceivedDate,
                j.JobCardRef      AS JobCardRef,
                COALESCE(q.QuotationTotal, 0) AS QuotationTotal,
                COALESCE(i.InvoiceTotal, 0)   AS InvoiceTotal
            FROM tbl_jobcarddetails j
            INNER JOIN (
                SELECT AssignedJobID,
                       SUM(
                         CASE
                           WHEN QuantityIssued IS NULL THEN Amount
                           ELSE QuantityIssued * Amount
                         END
                       ) AS QuotationTotal
                FROM tbl_quotation
                GROUP BY AssignedJobID
            ) q ON q.AssignedJobID = j.ID
            INNER JOIN (
                SELECT AssignedJobID,
                       SUM(
                         CASE
                           WHEN QuantityIssued IS NULL THEN Amount
                           ELSE QuantityIssued * Amount
                         END
                       ) AS InvoiceTotal
                FROM tbl_invoices
                GROUP BY AssignedJobID
            ) i ON i.AssignedJobID = j.ID
            WHERE 1=1
        """

        params = []

        if jobcard_ref:
            query += " AND j.JobCardRef LIKE %s"
            params.append(f"%{jobcard_ref}%")  # <-- partial match

        if start_date and end_date:
            query += " AND j.ReceivedDate BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND j.ReceivedDate >= %s"
            params.append(start_date)
        elif end_date:
            query += " AND j.ReceivedDate <= %s"
            params.append(end_date)

        query += " ORDER BY j.ReceivedDate DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]

    # Convert tuples to dicts, add No
    output = []
    for no, tup in enumerate(rows, start=1):
        r = dict(zip(cols, tup))
        output.append(
            {
                "No": no,
                "ID": r["ID"],
                "ReceivedDate": r["ReceivedDate"],
                "JobCardRef": r["JobCardRef"],
                "QuotationTotal": f"{float(r['QuotationTotal'] or 0):,.2f}",
                "InvoiceTotal": f"{float(r['InvoiceTotal'] or 0):,.2f}",
            }
        )

    return output


# *************************************************** Client Payment Summary Section ************************************
@anvil.server.callable()
def get_client_payment_summary(search_term=None, start_date=None, end_date=None):
    """
    Returns payment summary per JobCard with optional search term and date range.
    - No (enumerate)
    - Fullname
    - Phone
    - JobCardRef
    - ReceivedDate
    - TotalPaid (SUM of AmountPaid for the JobCardRefID)
    - Discount (latest Discount value for the JobCardRefID)
    - Balance (latest Balance value for the JobCardRefID)
    """

    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                tbl_clientcontacts.Fullname,
                tbl_clientcontacts.Phone,
                tbl_jobcarddetails.JobCardRef,
                tbl_jobcarddetails.ReceivedDate,
                SUM(tbl_payments.AmountPaid) AS TotalPaid,
                MAX(tbl_payments.Discount)   AS Discount,
                lp.Balance                   AS LatestBalance
            FROM tbl_payments 
            INNER JOIN tbl_jobcarddetails  
                ON tbl_jobcarddetails.ID = tbl_payments.JobCardRefID
            INNER JOIN tbl_clientcontacts  
                ON tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails
            LEFT JOIN (
                SELECT p1.JobCardRefID, p1.Balance
                FROM tbl_payments p1
                INNER JOIN (
                    SELECT JobCardRefID, MAX(ID) AS MaxID
                    FROM tbl_payments
                    GROUP BY JobCardRefID
                ) pmax ON p1.ID = pmax.MaxID
            ) lp ON lp.JobCardRefID = tbl_jobcarddetails.ID
            WHERE 1=1
        """

        params = []

        # Optional search filter
        if search_term:
            query += " AND (tbl_clientcontacts.Fullname LIKE %s OR tbl_clientcontacts.Phone LIKE %s OR tbl_jobcarddetails.RegNo LIKE %s)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

        # Optional date filters
        if start_date and end_date:
            query += " AND tbl_jobcarddetails.ReceivedDate BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND tbl_jobcarddetails.ReceivedDate >= %s"
            params.append(start_date)
        elif end_date:
            query += " AND tbl_jobcarddetails.ReceivedDate <= %s"
            params.append(end_date)

        query += """
            GROUP BY tbl_clientcontacts.Fullname, tbl_clientcontacts.Phone, tbl_jobcarddetails.JobCardRef, tbl_jobcarddetails.ReceivedDate, tbl_jobcarddetails.ID, lp.Balance
            ORDER BY tbl_jobcarddetails.ReceivedDate DESC
        """

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cols = [col[0] for col in cursor.description]

    # Convert rows to dicts and add No
    results = []
    for no, tup in enumerate(rows, start=1):
        r = dict(zip(cols, tup))
        results.append(
            {
                "No": no,
                "JobReceivedDate": (
                    r["ReceivedDate"].strftime("%Y-%m-%d")
                    if r["ReceivedDate"]
                    else None
                ),
                "JobCardRef": r["JobCardRef"],
                "Fullname": r["Fullname"],
                "Phone": r["Phone"],
                "TotalPaid": f"{float(r['TotalPaid'] or 0):,.2f}",
                "Discount": f"{float(r['Discount'] or 0):,.2f}",
                "Balance": f"{float(r['LatestBalance'] or 0):,.2f}",
            }
        )

    return results


# ***************************************************** Update Payment Details After Invoice Changes Section ************************************
@anvil.server.callable()
def updatePaymentDetailsAfterInvoiceChanges(jobcard_id):
    _get_current_user()

    invoiceDetails = get_invoice_details_by_job_id(jobcard_id)
    invoiceTotal = sum(float(row['Total'] or 0) for row in invoiceDetails)

    with db_cursor() as cursor:

        # Step 1: Get payments ordered DESC (latest first)
        cursor.execute("""
            SELECT 
                ID, AmountPaid, Discount
            FROM tbl_payments
            WHERE JobCardRefID = %s
            ORDER BY ID
        """, (jobcard_id,))

        payments = cursor.fetchall()

        if not payments:
            return []

        # Step 2: Recalculate balances
        running_balance = invoiceTotal
        updated_results = []

        for row in payments:
            payment_id = row[0]
            amount_paid = float(row[1] or 0)
            discount = float(row[2] or 0)

            # Calculate new balance
            new_balance = running_balance - amount_paid - discount

            # Prevent negative balance (optional safety)
            if new_balance < 0:
                new_balance = 0

            # Update DB
            cursor.execute("""
                UPDATE tbl_payments
                SET Balance = %s
                WHERE ID = %s
            """, (new_balance, payment_id))

            # Update running balance for next row
            running_balance = new_balance

__all__ = [
    'getInvoiceJobCardDetails',
    'saveInvoice',
    'get_invoice_details_by_job_id',
    'getJobcardEitherInQuotesOrPendingInvoices',
    'get_invoice_total_by_job_id',
    'update_invoice_status',
    'get_invoice_totals_and_counts_by_date',
    'getJobCardRefInvoiceDetails',
    'updateInvoice',
    'getInvoiceStatus',
    'get_previous_payment',
    'get_discount_payment',
    'save_payment_details',
    'getPaidPendingInvoices',
    'getPaymentsDetails',
    'delete_payment',
    'get_payment_ref',
    'fillReportData',
    'createReportPdf',
    'get_jobcard_quote_invoice_totals',
    'get_client_payment_summary',
    'updatePaymentDetailsAfterInvoiceChanges',
]

from . import BMALocal as _compatibility_facade
