from ._common import *

# ***************************************************Quotation Details Section ************************************

@anvil.server.callable()
def getDuplicateQuotationEntries(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                COUNT(*) as Entries
            FROM 
                tbl_techniciandefectsandrequestedparts 
            WHERE 
                tbl_techniciandefectsandrequestedparts.JobCardRefID=%s;
        """
        cursor.execute(query, (valueID,))
        result = cursor.fetchone()
        return result[0] if result else 0  # Return the count of entries or 0 if no result
    
@anvil.server.callable()
def displayDuplicateQuotationEntries(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                tbl_techniciandefectsandrequestedparts.ID,
                tbl_jobcarddetails.JobCardRef,
                tbl_techniciandefectsandrequestedparts.TechnicianPortalRequestedParts,
                tbl_techniciandefectsandrequestedparts.Defects,
                tbl_techniciandefectsandrequestedparts.PricedDefectsList,
                tbl_techniciandefectsandrequestedparts.RequestedParts,
                tbl_techniciandefectsandrequestedparts.PreparedByStaff
            FROM
                tbl_techniciandefectsandrequestedparts
            INNER JOIN tbl_jobcarddetails
                ON tbl_techniciandefectsandrequestedparts.JobCardRefID = tbl_jobcarddetails.ID
            WHERE
                tbl_techniciandefectsandrequestedparts.JobCardRefID = %s;
        """
        cursor.execute(query, (valueID,))
        results = cursor.fetchall()
        return [
            {
                "ID": r[0],
                "JobCardRef": r[1],
                "TechnicianRequestedParts": r[2],
                "Defects": r[3],
                "PricedDefects": r[4],
                "RequestedParts": str(r[5]),
                "CreatedBy": r[6],
            }
            for r in results
        ]

@anvil.server.callable()
def deleteDuplicateQuotationEntry(entryID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            DELETE FROM tbl_techniciandefectsandrequestedparts
            WHERE ID = %s
        """
        cursor.execute(query, (entryID,))

@anvil.server.callable()
def getQuotationJobCardDetails():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT DISTINCT tbl_jobcarddetails.JobCardRef, tbl_quotation.AssignedJobID
            FROM tbl_quotation 
            INNER JOIN tbl_jobcarddetails 
            ON tbl_quotation.AssignedJobID = tbl_jobcarddetails.ID
            ORDER BY tbl_jobcarddetails.JobCardRef;
        """

        cursor.execute(query)
        result = cursor.fetchall()
        return [{"JobCardRef": r[0], "ID": r[1]} for r in result]


@anvil.server.callable()
def saveQuotationPartsAndServices(
    assignedDate, jobCardID, name, number, quantity, amount
):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_quotation (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount)
            VALUES (%s,%s,%s,%s, %s, %s)
        """
        cursor.execute(query, (assignedDate, jobCardID, name, number, quantity, amount))


@anvil.server.callable()
def save_quotation_parts_and_services_batch(assignedDate, jobCardID, items):
    """Batch insert multiple quotation parts/services in a single SQL operation."""
    _get_current_user()
    if not items:
        return
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_quotation (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        data = [
            (
                assignedDate,
                jobCardID,
                it.get("name") or it.get("Name", ""),
                it.get("number") or it.get("Number", ""),
                it.get("quantity") if it.get("quantity") is not None else it.get("Quantity"),
                it.get("amount") if it.get("amount") is not None else it.get("Amount", 0.0),
            )
            for it in items
        ]
        cursor.executemany(query, data)


@anvil.server.callable()
def get_quote_details_by_job_id(job_id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
        SELECT
            tbl_clientcontacts.Fullname,
            tbl_jobcarddetails.MakeAndModel,
            tbl_jobcarddetails.RegNo,
            tbl_quotation.Date,
            tbl_jobcarddetails.ChassisNo,
            tbl_jobcarddetails.EngineCode,
            tbl_jobcarddetails.Mileage,
            tbl_quotation.Item,
            tbl_quotation.QuantityIssued,
            tbl_quotation.Amount,
            tbl_quotation.AssignedJobID
        FROM
            (tbl_jobcarddetails
            INNER JOIN tbl_clientcontacts
            ON tbl_jobcarddetails.ClientDetails = tbl_clientcontacts.ID)
        INNER JOIN tbl_quotation
            ON tbl_jobcarddetails.ID = tbl_quotation.AssignedJobID
        WHERE tbl_quotation.AssignedJobID = %s
        """
        cursor.execute(query, (job_id,))
        rows = cursor.fetchall()

        result = []
        for r in rows:
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

            quantity_issued_val = safe_float_convert(r[8])  # QuantityIssued
            amount_val = safe_float_convert(r[9])  # Amount

            # Ensure 'QuantityIssued' for the dictionary can be "" if originally None or non-numeric string
            # If your front-end expects an empty string, keep this logic
            display_quantity_issued = (
                ""
                if r[8] is None or not isinstance(r[8], (int, float, decimal.Decimal))
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
                    "Fullname": r[0],
                    "MakeAndModel": r[1],
                    "RegNo": r[2],
                    "Date": r[3],
                    "ChassisNo": r[4],
                    "EngineCode": r[5],
                    "Mileage": r[6],
                    "Item": r[7],
                    "QuantityIssued": display_quantity_issued,  # Use the potentially "" value for display
                    "Amount": amount_val,  # This is now always a float or None
                    "AssignedJobID": r[10],
                    "Total": total_calc,  # This is now always a float or None
                }
            )

        return result


@anvil.server.callable()
def get_quote_confirmation_details_by_job_id(job_id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
        SELECT
            tbl_clientcontacts.Fullname,
            tbl_jobcarddetails.MakeAndModel,
            tbl_jobcarddetails.RegNo,
            tbl_quotationpartsandservicesfeedback.Date,
            tbl_jobcarddetails.ChassisNo,
            tbl_jobcarddetails.EngineCode,
            tbl_jobcarddetails.Mileage,
            tbl_quotationpartsandservicesfeedback.Item,
            tbl_quotationpartsandservicesfeedback.QuantityIssued,
            tbl_quotationpartsandservicesfeedback.Amount,
            tbl_quotationpartsandservicesfeedback.AssignedJobID
        FROM
            (tbl_jobcarddetails
            INNER JOIN tbl_clientcontacts
            ON tbl_jobcarddetails.ClientDetails = tbl_clientcontacts.ID)
        INNER JOIN tbl_quotationpartsandservicesfeedback
            ON tbl_jobcarddetails.ID = tbl_quotationpartsandservicesfeedback.AssignedJobID
        WHERE tbl_quotationpartsandservicesfeedback.AssignedJobID = %s
        """
        cursor.execute(query, (job_id,))
        rows = cursor.fetchall()

        result = []
        for r in rows:
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

            quantity_issued_val = safe_float_convert(r[8])  # QuantityIssued
            amount_val = safe_float_convert(r[9])  # Amount

            # Ensure 'QuantityIssued' for the dictionary can be "" if originally None or non-numeric string
            # If your front-end expects an empty string, keep this logic
            display_quantity_issued = (
                ""
                if r[8] is None or not isinstance(r[8], (int, float, decimal.Decimal))
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
                    "Fullname": r[0],
                    "MakeAndModel": r[1],
                    "RegNo": r[2],
                    "Date": r[3],
                    "ChassisNo": r[4],
                    "EngineCode": r[5],
                    "Mileage": r[6],
                    "Item": r[7],
                    "QuantityIssued": display_quantity_issued,  # Use the potentially "" value for display
                    "Amount": amount_val,  # This is now always a float or None
                    "AssignedJobID": r[10],
                    "Total": total_calc,  # This is now always a float or None
                }
            )

        return result

@anvil.server.callable()
def get_interimandquotation_total_by_job_id(assigned_job_id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT SUM(
                COALESCE(QuantityIssued, 1) * Amount
            ) AS GrandTotal
            FROM tbl_quotation
            WHERE AssignedJobID = %s
        """
        cursor.execute(query, (assigned_job_id,))
        result = cursor.fetchone()
        return f"{float(result[0]):,.2f}" if result and result[0] is not None else 0.0

@anvil.server.callable()
def get_defects_list_details_by_job_id(jobCardID):
    """
    Returns detailed job card information including:
      - Client name
      - Vehicle details
      - Technician name
      - Cleaned and enumerated defects list
    """
    _get_current_user()
    with db_cursor() as cursor:
        query1 = """
            SELECT 
                tbl_clientcontacts.Fullname AS ClientName,
                tbl_jobcarddetails.RegNo,
                tbl_jobcarddetails.MakeAndModel,
                tbl_jobcarddetails.EngineCode,
                tbl_jobcarddetails.ChassisNo,
                tbl_jobcarddetails.ReceivedDate,
                tbl_technicians.Fullname AS TechnicianName,
                tbl_techniciandefectsandrequestedparts.Defects,
                tbl_checkstaff.Staff AS PreparedByStaff,
                tbl_techniciandefectsandrequestedparts.Signature
            FROM tbl_jobcarddetails
            JOIN tbl_clientcontacts 
                ON tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails
            JOIN tbl_pendingassignedjobs 
                ON tbl_pendingassignedjobs.JobCardRefID = tbl_jobcarddetails.ID
            JOIN tbl_technicians 
                ON tbl_technicians.ID = tbl_pendingassignedjobs.TechnicianID
            JOIN tbl_techniciandefectsandrequestedparts 
                ON tbl_techniciandefectsandrequestedparts.JobCardRefID = tbl_jobcarddetails.ID
            JOIN tbl_checkstaff
                ON tbl_checkstaff.Staff = tbl_techniciandefectsandrequestedparts.PreparedByStaff
            WHERE tbl_jobcarddetails.ID = %s;

        """
        cursor.execute(query1, (jobCardID,))
        result1 = cursor.fetchone()

        query2 = """
            SELECT 
                tbl_clientcontacts.Fullname AS ClientName,
                tbl_jobcarddetails.RegNo,
                tbl_jobcarddetails.MakeAndModel,
                tbl_jobcarddetails.EngineCode,
                tbl_jobcarddetails.ChassisNo,
                tbl_jobcarddetails.ReceivedDate,
                tbl_technicians.Fullname AS TechnicianName,
                tbl_techniciandefectsandrequestedparts.Defects,
                tbl_technicians.Fullname AS PreparedByStaff,
                tbl_techniciandefectsandrequestedparts.Signature
            FROM tbl_jobcarddetails
            JOIN tbl_clientcontacts 
                ON tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails
            JOIN tbl_pendingassignedjobs 
                ON tbl_pendingassignedjobs.JobCardRefID = tbl_jobcarddetails.ID
            JOIN tbl_techniciandefectsandrequestedparts 
                ON tbl_techniciandefectsandrequestedparts.JobCardRefID = tbl_jobcarddetails.ID
            JOIN tbl_technicians
                ON tbl_technicians.Fullname = tbl_techniciandefectsandrequestedparts.PreparedByStaff
            WHERE tbl_jobcarddetails.ID = %s;
            """
        cursor.execute(query2, (jobCardID,))
        result2 = cursor.fetchone()
        if result1 is None and result2 is None:
            return None  # No data found for the given JobCardID
        elif result1 is not None:   
            result = result1
        else:
            result = result2    

        # Unpack query result
        (
            client_name,
            reg_no,
            make_model,
            engine_code,
            chassis_no,
            received_date,
            technician_name,
            raw_defects,
            staff,
            signature,
        ) = result

        # --- Clean and process defects text ---
        if raw_defects:
            # Step 1: Remove HTML tags (<div>, <br>, etc.)
            text_only = re.sub(r"<[^>]+>", "", raw_defects)

            # Step 2: Split into lines, remove empty ones
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Enumerate defects
            numbered_defects = [
                {"No": i + 1, "Defect": line} for i, line in enumerate(lines)
            ]
        else:
            numbered_defects = []

        # If Signature is stored as BLOB → convert to base64
        if isinstance(signature, (bytes, bytearray)):
            signature_b64 = base64.b64encode(signature).decode("utf-8")

        # --- Return combined data ---
        return {
            "ClientName": client_name,
            "RegNo": reg_no,
            "MakeAndModel": make_model,
            "EngineCode": engine_code,
            "ChassisNo": chassis_no,
            "ReceivedDate": str(received_date),
            "TechnicianName": technician_name,
            "Defects": numbered_defects,
            "Staff": staff,
            "Signature": signature_b64,
        }


@anvil.server.callable()
def get_priced_defects_list_details_by_job_id(jobCardID):
    """
    Returns detailed job card information including:
      - Client name
      - Vehicle details
      - Technician name
      - Cleaned and enumerated priced defects list
    """
    _get_current_user()
    with db_cursor() as cursor:
        query1 = """
            SELECT 
                tbl_clientcontacts.Fullname AS ClientName,
                tbl_jobcarddetails.RegNo,
                tbl_jobcarddetails.MakeAndModel,
                tbl_jobcarddetails.EngineCode,
                tbl_jobcarddetails.ChassisNo,
                tbl_jobcarddetails.ReceivedDate,
                tbl_technicians.Fullname AS TechnicianName,
                tbl_techniciandefectsandrequestedparts.PricedDefectsList,
                tbl_checkstaff.Staff AS PreparedByStaff,
                tbl_techniciandefectsandrequestedparts.Signature
            FROM tbl_jobcarddetails
            JOIN tbl_clientcontacts 
                ON tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails
            JOIN tbl_pendingassignedjobs 
                ON tbl_pendingassignedjobs.JobCardRefID = tbl_jobcarddetails.ID
            JOIN tbl_technicians 
                ON tbl_technicians.ID = tbl_pendingassignedjobs.TechnicianID
            JOIN tbl_techniciandefectsandrequestedparts 
                ON tbl_techniciandefectsandrequestedparts.JobCardRefID = tbl_jobcarddetails.ID
            JOIN tbl_checkstaff
                ON tbl_checkstaff.Staff = tbl_techniciandefectsandrequestedparts.PreparedByStaff
            WHERE tbl_jobcarddetails.ID = %s;

        """
        cursor.execute(query1, (jobCardID,))
        result1 = cursor.fetchone()

        query2 = """
            SELECT 
                tbl_clientcontacts.Fullname AS ClientName,
                tbl_jobcarddetails.RegNo,
                tbl_jobcarddetails.MakeAndModel,
                tbl_jobcarddetails.EngineCode,
                tbl_jobcarddetails.ChassisNo,
                tbl_jobcarddetails.ReceivedDate,
                tbl_technicians.Fullname AS TechnicianName,
                tbl_techniciandefectsandrequestedparts.PricedDefectsList,
                tbl_technicians.Fullname AS PreparedByStaff,
                tbl_techniciandefectsandrequestedparts.Signature
            FROM tbl_jobcarddetails
            JOIN tbl_clientcontacts 
                ON tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails
            JOIN tbl_pendingassignedjobs 
                ON tbl_pendingassignedjobs.JobCardRefID = tbl_jobcarddetails.ID
            JOIN tbl_techniciandefectsandrequestedparts 
                ON tbl_techniciandefectsandrequestedparts.JobCardRefID = tbl_jobcarddetails.ID
            JOIN tbl_technicians
                ON tbl_technicians.Fullname = tbl_techniciandefectsandrequestedparts.PreparedByStaff
            WHERE tbl_jobcarddetails.ID = %s;
            """
        cursor.execute(query2, (jobCardID,))
        result2 = cursor.fetchone()
        if result1 is None and result2 is None:
            return None  # No data found for the given JobCardID
        elif result1 is not None:   
            result = result1
        else:
            result = result2    

        # Unpack query result
        (
            client_name,
            reg_no,
            make_model,
            engine_code,
            chassis_no,
            received_date,
            technician_name,
            raw_defects,
            staff,
            signature,
        ) = result

        # --- Clean and process defects text ---
        if raw_defects:
            # Step 1: Remove HTML tags (<div>, <br>, etc.)
            text_only = re.sub(r"<[^>]+>", "", raw_defects)

            # Step 2: Split into lines, remove empty ones
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Enumerate defects
            numbered_defects = [
                {"No": i + 1, "Defect": line} for i, line in enumerate(lines)
            ]
        else:
            numbered_defects = []

        # If Signature is stored as BLOB → convert to base64
        if isinstance(signature, (bytes, bytearray)):
            signature_b64 = base64.b64encode(signature).decode("utf-8")

        # --- Return combined data ---
        return {
            "ClientName": client_name,
            "RegNo": reg_no,
            "MakeAndModel": make_model,
            "EngineCode": engine_code,
            "ChassisNo": chassis_no,
            "ReceivedDate": str(received_date),
            "TechnicianName": technician_name,
            "Defects": numbered_defects,
            "Staff": staff,
            "Signature": signature_b64,
        }


@anvil.server.callable()
def getDepositPaidOnQuotesAndPendingInvoices(jobcardrefId):
    _get_current_user()

    with db_cursor() as cursor:
        query = """
            SELECT COALESCE(SUM(AmountPaid), 0)
            FROM tbl_payments
            WHERE JobCardRefID = %s
        """

        cursor.execute(query, (jobcardrefId,))
        row = cursor.fetchone()

        return float(row[0]) if row and row[0] is not None else 0


@anvil.server.callable()
def fillQuotationInvoiceData(
    jobCardID, docType, logo_path: str = None, font_path: str = None
) -> str:
    _get_current_user()

    if logo_path is None:
        logo_path = os.getenv("LOGO")
    if font_path is None:
        font_path = os.getenv("FONT_PATH") or os.getenv("FONT")

    # === Get document details ===
    if docType == "Quotation":
        docTitle = "Quotation"
        vehicledetails = get_quote_details_by_job_id(jobCardID)
    elif docType == "InterimQuotation":
        docTitle = "Interim Quotation"
        vehicledetails = get_quote_details_by_job_id(jobCardID)
    elif docType == "Invoice":
        docTitle = "Invoice"
        vehicledetails = get_invoice_details_by_job_id(jobCardID)
    elif docType == "Confirm Quotation":
        docTitle = "Confirm Quotation"
        vehicledetails = get_quote_confirmation_details_by_job_id(jobCardID)
        if not vehicledetails:
            vehicledetails = get_quote_details_by_job_id(jobCardID)
    else:
        docTitle = docType
        vehicledetails = []

    v0 = vehicledetails[0] if vehicledetails else {
        "Fullname": "",
        "MakeAndModel": "",
        "RegNo": "",
        "Date": "",
        "ChassisNo": "",
        "EngineCode": "",
        "Mileage": ""
    }

    # === Embed Mozilla Headline font as base64 ===
    font_base64 = ""
    font_face_css = ""

    if font_path and os.path.exists(font_path):
        with open(font_path, "rb") as f:
            font_base64 = base64.b64encode(f.read()).decode("utf-8")

        font_face_css = f"""
        @font-face {{
            font-family: 'Mozilla Headline';
            src: url(data:font/ttf;base64,{font_base64}) format('truetype');
        }}
        """

    # === Handle company logo ===
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as logo_file:
            logo_base64 = base64.b64encode(
                logo_file.read()
            ).decode("utf-8")

        logo_img_tag = (
            f'<img src="data:image/png;base64,{logo_base64}" '
            f'alt="Company Logo" '
            f'style="width: 100%; height: 100%; border-radius: 2px;">'
        )
    else:
        logo_img_tag = "LOGO"

    # =========================================================
    # CALCULATE TOTALS AND CONDITIONALLY GENERATE FOOTER ROWS
    # =========================================================

    sub_total = sum(
        float(item["Total"])
        for item in vehicledetails
        if item.get("Total") is not None
    )

    previous_balance = 0.0

    # Get total payments made against this job card
    deposit_balance = float(
        getDepositPaidOnQuotesAndPendingInvoices(jobCardID) or 0
    )

    footer_total_details = ""

    # Find Previous Balance and exclude it from the item subtotal
    for item in vehicledetails:
        if item.get("Item") == "Previous Balance":
            previous_balance = float(item.get("Amount") or 0)

            sub_total -= previous_balance
            break

    # Show the footer details only if either balance is non-zero
    if previous_balance != 0 or deposit_balance != 0:

        # Subtotal row
        footer_total_details = f"""
            <tr class="total-row">
                <td colspan="4"
                    style="text-align: right; font-weight: 500;">
                    Sub Total
                </td>
                <td style="font-weight: 500;">
                    {sub_total:,.2f}
                </td>
            </tr>
        """

        # Previous Balance row: show only when non-zero
        if previous_balance != 0:
            footer_total_details += f"""
                <tr class="total-row">
                    <td colspan="4"
                        style="text-align: right; font-weight: 500;">
                        Previous Balance
                    </td>
                    <td style="font-weight: 500;">
                        {previous_balance:,.2f}
                    </td>
                </tr>
            """

        # Deposit row: show only when non-zero
        if deposit_balance != 0:
            footer_total_details += f"""
                <tr class="total-row">
                    <td colspan="4"
                        style="text-align: right; font-weight: 500;">
                        (Payment)
                    </td>
                    <td style="font-weight: 500;">
                        {deposit_balance:,.2f}
                    </td>
                </tr>
            """

    # Grand Total = current items + previous balance - deposits paid
    grand_total = (
        sub_total
        + previous_balance
        - deposit_balance
    )

    # Determine the final row label
    total_label = (
        "Balance"
        if previous_balance != 0 or deposit_balance != 0
        else "Grand Total"
    )

    # === Generate item table rows ===
    items_html = ""
    counter = 0

    for item in vehicledetails:
        counter += 1

        if item["Amount"] == 0:
            textAmount = "TO BE CONFIRMED"
        else:
            textAmount = f"{item['Amount']:,.2f}"

        if item["Total"] == 0:
            textTotal = "TO BE CONFIRMED"
        else:
            textTotal = f"{item['Total']:,.2f}"

        # Do not display Previous Balance as an item
        if item["Item"] != "Previous Balance":
            items_html += f"""
                <tr class="item-row">
                    <td>{counter}</td>
                    <td>{html_module.escape(str(item['Item']))}</td>
                    <td>{html_module.escape(str(item['QuantityIssued']))}</td>
                    <td>{textAmount}</td>
                    <td>{textTotal}</td>
                </tr>
            """

    # === Document notes ===
    if docType in ("Quotation", "InterimQuotation"):
        quotationNotes = """
            <div class="notes-section">
                <div class="notes-title">
                    NOTE: THE ABOVE ESTIMATE IS SUBJECT TO REVIEW DUE TO:
                </div>
                <ol class="notes-list">
                    <li>Price change at the time of actual repair</li>
                    <li>Further damages found during repairs</li>
                    <li>100% Deposit on imported parts</li>
                    <li>70% deposit on local parts on commencement</li>
                </ol>
            </div>
        """
    else:
        quotationNotes = """
            <div class="notes-section">
                <div class="notes-title">NOTES:</div>
                <ol class="notes-list">
                    <li>Thank you for choosing BMW CENTER LIMITED</li>
                    <li>Cheque Address to: BMW CENTER LIMITED</li>
                </ol>
            </div>
        """

    # === Complete HTML template ===
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{docTitle}</title>
    <style>
        {font_face_css}

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
            background: linear-gradient(
                135deg, #228B22, #90EE90, #FFD700, #FF6347
            );
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
            grid-template-columns: 140px 1fr;
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

        #footer div {{
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

        <table style="width: 100%; table-layout: fixed; margin: 24px 0;">
            <tr>
                <td style="width: 50%; vertical-align: top;
                           padding-left: 24px; padding-right: 32px;">
                    <div class="detail-row">
                        <span class="detail-label">Customer Name:</span>
                        <div>
                            <span class="detail-value">{v0['Fullname']}</span>
                        </div>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">Make And Model:</span>
                        <div>
                            <span class="detail-value">{v0['MakeAndModel']}</span>
                        </div>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">Reg No:</span>
                        <div>
                            <span class="detail-value">{v0['RegNo']}</span>
                        </div>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <div>
                            <span class="detail-value">{v0['Date']}</span>
                        </div>
                    </div>
                </td>

                <td style="width: 50%; vertical-align: top;
                           padding-left: 32px;">
                    <div class="detail-row">
                        <span class="detail-label">Chassis:</span>
                        <div>
                            <span class="detail-value">{v0['ChassisNo']}</span>
                        </div>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">Engine:</span>
                        <div>
                            <span class="detail-value">{v0['EngineCode']}</span>
                        </div>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">Mileage:</span>
                        <div>
                            <span class="detail-value">{v0['Mileage']}</span>
                        </div>
                    </div>

                    <div class="detail-row">
                        <span class="detail-label">&nbsp;</span>
                        <span class="detail-value">&nbsp;</span>
                    </div>
                </td>
            </tr>
        </table>

        <table class="items-table">
            <thead>
                <tr>
                    <th>No.</th>
                    <th>Item</th>
                    <th>Quantity</th>
                    <th>Amount (Kshs)</th>
                    <th>Total (Kshs)</th>
                </tr>
            </thead>
            <tbody>
                {items_html}

                {footer_total_details}

                <tr class="total-row">
                    <td colspan="4"
                        style="text-align: right; font-weight: 500;">
                        {total_label}
                    </td>
                    <td style="font-weight: 500;">
                        {grand_total:,.2f}
                    </td>
                </tr>
            </tbody>
        </table>

        {quotationNotes}

        <footer id="footer">
            <div>
                <p>
                    Joy Is The Feeling Of Being Looked After By The Best -
                    BMW CENTER For Your BMW.
                </p>
            </div>
        </footer>

    </div>
</body>
</html>
"""

    return html_content


@anvil.server.callable()
def createQuotationInvoicePdf(jobCardID, docType):
    _get_current_user()
    try:
        docName = getQuotationInvoiceName(jobCardID)
        if docType == "Quotation":
            fileName = str(docName) + " Quotation"
        elif docType == "InterimQuotation":
            fileName = str(docName) + " Interim Quote"
        elif docType == "Invoice":
            fileName = str(docName) + " Invoice"
        elif docType == "Confirm Quotation":
            fileName = str(docName) + " Confirm Quotation"

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
            "load-error-handling": "ignore",
            "load-media-error-handling": "ignore",
            "quiet": "",
        }

        html_string = fillQuotationInvoiceData(jobCardID, docType)
        get_pdfkit().from_string(
            html_string, fileName, options=setting_options, configuration=get_pdfkit_config()
        )
        media_object = anvil.media.from_file(fileName, "application/pdf", name=fileName)
        return media_object

    except Exception as e:
        print("PDF generation failed:", str(e))
        raise


@anvil.server.callable()
def deleteFile(jobCardID, docType):
    _get_current_user()
    docName = getQuotationInvoiceName(jobCardID)
    
    if docType == "Quotation":
        fileName = str(docName) + " Quotation"
    elif docType == "Confirm Quotation":
        fileName = str(docName) + " Confirm Quotation"
    elif docType == "InterimQuotation":
        fileName = str(docName) + " Interim Quote"
    elif docType == "Invoice":
        fileName = str(docName) + " Invoice"
    elif docType == "Payment":
        fileName = str(docName) + " Payment"
    elif docType == "Jobcard":
        fileName = str(docName) + " Jobcard"
    elif docType == "TechNotes":
        fileName = str(docName) + " Technician Notes"
    elif docType == "DefectsList":
        result = getJobCardRow(jobCardID)
        fileName = str(result["JobCardRef"]) + " Defects List"
    elif docType == "PricedDefectsList":
        result = getJobCardRow(jobCardID)
        fileName = str(result["JobCardRef"]) + " Priced Defects List"
    elif docType == "InspectionChecklist":
        fileName = str(docName) + " Inspection Checklist"

    if os.path.exists(fileName):
        os.remove(fileName)
        print("File deleted successfully.")
    else:
        print("File does not exist.")


@anvil.server.callable()
def populate_confirmation_from_quote(jobcardID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Item, Part_No, QuantityIssued, Amount 
            FROM tbl_quotation
            WHERE AssignedJobID = %s
            ORDER BY tbl_quotation.ID
        """
        cursor.execute(query, (jobcardID,))
        results = cursor.fetchall() or []

        # Return as a list of dictionaries
        return [
            {
                "Name": r[0],
                "Number": r[1],
                "Quantity": r[2],
                "Amount": f"{float(r[3]):,.2f}",
            }
            for r in results
        ]


# ***************************************************Quotation Feedback Details Section ************************************

@anvil.server.callable()
def saveFullQuotationPartsAndServicesFeedback(assignedDate, jobCardID, remarks, items):
    _get_current_user()
    with db_cursor() as cursor:

        # Step 1: Delete existing feedback records for the job card
        cursor.execute(
            "DELETE FROM tbl_quotationpartsandservicesfeedback WHERE AssignedJobID = %s",
            (jobCardID,),
        )
        cursor.execute(
            "DELETE FROM tbl_clientquotationfeedback WHERE AssignedJobID = %s",
            (jobCardID,),
        )

        # Step 2: Insert one feedback record
        cursor.execute(
            """
            INSERT INTO tbl_clientquotationfeedback (AssignedJobID, Remarks)
            VALUES (%s, %s)
        """,
            (jobCardID, remarks),
        )

        # Step 3: Get the last inserted ID
        feedback_id = cursor.lastrowid

        # Step 4: Insert all items linked to the single feedback ID
        insert_item = """
            INSERT INTO tbl_quotationpartsandservicesfeedback 
            (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount, ClientQuotationFeedbackID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for item in items:
            cursor.execute(
                insert_item,
                (
                    assignedDate,
                    jobCardID,
                    item["name"],
                    item["number"],
                    item["quantity"],
                    item["amount"],
                    feedback_id,
                ),
            )

        return {"status": "success", "feedback_id": feedback_id}

@anvil.server.callable()
def updateQuotationPartsAndServices(assignedDate, jobCardID, items):
    _get_current_user()
    with db_cursor() as cursor:
        # Step 1: Delete existing feedback records for the job card
        cursor.execute(
            "DELETE FROM tbl_quotationpartsandservicesfeedback WHERE AssignedJobID = %s",
            (jobCardID,),
        )
        # Step 2: Get Client Quotation Feedback ID
        cursor.execute(
            "SELECT ID FROM tbl_clientquotationfeedback WHERE AssignedJobID = %s",
            (jobCardID,),
        )

        row = cursor.fetchone()

        if not row:
            raise Exception("No client quotation feedback found for this JobCard.")

        feedback_id = row[0]
 
        # Step 3: Insert all items linked to the single feedback ID
        insert_item = """
            INSERT INTO tbl_quotationpartsandservicesfeedback 
            (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount, ClientQuotationFeedbackID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for item in items:
            cursor.execute(
                insert_item,
                (
                    assignedDate,
                    jobCardID,
                    item["name"],
                    item["number"],
                    item["quantity"],
                    item["amount"],
                    feedback_id,
                ),
            )

        return {"status": "success", "feedback_id": feedback_id}

@anvil.server.callable()
def getClientQuotationFeedback(JobCardID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
        SELECT ID FROM tbl_clientquotationfeedback WHERE AssignedJobID = %s
        """
        cursor.execute(query, (JobCardID,))
        result = cursor.fetchone()

        if not result:
            return "No feedback found"

        feedback_id = result[0]

        query2 = """
        SELECT Item, QuantityIssued AS Quantity 
        FROM tbl_quotationpartsandservicesfeedback 
        WHERE ClientQuotationFeedbackID = %s
        """
        cursor.execute(query2, (feedback_id,))
        rows = cursor.fetchall()

        return [{"Item": row[0], "Quantity": row[1]} for row in rows]


@anvil.server.callable()
def getQuotationConfirmationFeedback(JobCardID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
        
            SELECT 
                tbl_quotationpartsandservicesfeedback.Item, tbl_quotationpartsandservicesfeedback.Part_No, 
                tbl_quotationpartsandservicesfeedback.QuantityIssued, tbl_quotationpartsandservicesfeedback.Amount, 
                tbl_carpartnames.ID AS CarPartID
            FROM 
                tbl_quotationpartsandservicesfeedback 
            LEFT JOIN 
                tbl_carpartnames ON tbl_quotationpartsandservicesfeedback.Part_No = tbl_carpartnames.PartNo
            WHERE 
                tbl_quotationpartsandservicesfeedback.AssignedJobID = %s
            ORDER BY
                tbl_quotationpartsandservicesfeedback.ID

        """
        cursor.execute(query, (JobCardID,))
        result = cursor.fetchall()

        if result:
            return [
                {
                    "Name": row[0],
                    "Number": row[1],
                    "Quantity": row[2],
                    "Amount": f"{float(row[3]):,.2f}",
                }
                for row in result
            ]
        else:
            return []


# *************************************************** Interim Quotation Details Section ************************************


@anvil.server.callable()
def saveJobCardDetailsFromInterimQuotation(
    customer_ID,
    job_card_ref,
    received_date,
    due_date,
    check_in_staff,
    reg_no,
    make_and_model,
    chassis,
    engine_code,
    mileage,
    oldJobCardID,
):
    _get_current_user()
    with db_cursor() as cursor:
        # Check if old job card ref ends with IQ
        result = getJobCardRef(oldJobCardID)
        # If it does, delete old quotation and job card for a fresh start
        if result and "JobCardRef" in result[0]:
            if result[0]["JobCardRef"].endswith("IQ"):
                # Delete old quotation if exists
                cursor.execute(
                    "DELETE FROM tbl_quotation WHERE AssignedJobID = %s",
                    (oldJobCardID,),
                )
                # Delete old job card if exists
                cursor.execute(
                    "DELETE FROM tbl_jobcarddetails WHERE ID = %s", (oldJobCardID,)
                )

        # Insert new job card details
        query = """
            INSERT INTO tbl_jobcarddetails
            (ClientDetails, JobCardRef, ReceivedDate, DueDate, CheckedInBy, 
             RegNo, MakeAndModel, ChassisNo, EngineCode, Mileage, 
             Ins, ClientInstruction, Notes, IsComplete) 
            VALUES (%s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                customer_ID,
                job_card_ref,
                received_date,
                due_date,
                check_in_staff,
                reg_no,
                make_and_model,
                chassis,
                engine_code,
                mileage,
                1,
                "None",
                "None",
                1,
            ),
        )
        return cursor.lastrowid


@anvil.server.callable()
def saveInterimQuotationPartsAndServices(assignedDate, jobCardID, items):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                INSERT INTO tbl_quotation (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
        for item in items:
            name = item.get("name", "")
            number = item.get("number", "")
            quantity = item.get("quantity")
            amount = item.get("amount")
            cursor.execute(
                query, (assignedDate, jobCardID, name, number, quantity, amount)
            )


@anvil.server.callable()
def getInterimQuoteAndAmendedInvoiceStaff():
    _get_current_user()
    def _load():
        with db_cursor() as cursor:
            query = """
                SELECT ID, Staff
                FROM tbl_checkstaff
                WHERE IsArchived = FALSE
                ORDER BY Staff ASC
            """
            cursor.execute(query)
            result = cursor.fetchall()
            # Return list of tuples: (label shown, value stored)
            return [(r[1], r[0]) for r in result]
    return list(cached_lookup("interim_staff", _load, ttl_seconds=300))


@anvil.server.callable()
def getPreviousInterimQuoteDetails(customerID, makeAndModel, chassis, receivedDate):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                j.ID,
                j.JobCardRef,
                j.ReceivedDate,
                j.RegNo,
                j.MakeAndModel,
                j.ChassisNo,
                j.EngineCode,
                j.Mileage,
                q.Item,
                q.Part_No,
                q.QuantityIssued,
                q.Amount
            FROM 
                tbl_jobcarddetails j
            LEFT JOIN 
                tbl_quotation q ON j.ID = q.AssignedJobID
            WHERE 
                j.ClientDetails = %s
                AND j.MakeAndModel = %s
                AND j.ChassisNo = %s
                AND j.ReceivedDate = %s
                AND q.Item IS NOT NULL  -- Only include rows with parts data
            ORDER BY 
                j.ReceivedDate DESC, j.ID DESC;
        """
        cursor.execute(query, (customerID, makeAndModel, chassis, receivedDate))
        rows = cursor.fetchall()  # Get all rows instead of just one

        if rows:
            # Get job details from first row
            job_details = {
                "JobCardID": rows[0][0],
                "JobCardRef": rows[0][1],
                "ReceivedDate": rows[0][2],
                "RegNo": rows[0][3],
                "MakeAndModel": rows[0][4],
                "ChassisNo": rows[0][5],
                "EngineCode": rows[0][6],
                "Mileage": rows[0][7],
            }

            # Create parts list
            parts_list = []
            for row in rows:
                if row[8] is not None:  # If Item exists
                    parts_list.append(
                        {
                            "Name": row[8],
                            "Number": row[9],
                            "Quantity": row[10],
                            "Amount": (
                                f"{float(row[11]):,.2f}"
                                if row[11] is not None
                                else "0.00"
                            ),
                        }
                    )

            return {"job_details": job_details, "parts": parts_list}
        else:
            return None


@anvil.server.callable()
def getInterimQuote(value):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, JobCardRef
            FROM tbl_jobcarddetails
            WHERE LOWER(JobCardRef) LIKE %s
              AND LOWER(JobCardRef) LIKE '%%-iq';
        """
        like_value = f"%{value.lower()}%"
        cursor.execute(query, (like_value,))
        results = cursor.fetchall()

        # Return in format suitable for dropdown: [(display_text, value), ...]
        return [(row[1], row[0]) for row in results]  # (JobCardRef, ID)


@anvil.server.callable()
def transitionInterimQuoteToInvoice(jocardID):
    _get_current_user()
    with db_cursor() as cursor:
        # Delete old invoice details
        cursor.execute("DELETE FROM tbl_invoices WHERE AssignedJobID = %s", (jocardID,))

        # Insert new invoice details from interim quotation
        query = """
            INSERT INTO tbl_invoices (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount, Status)
            SELECT Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount, 'Pending'
            FROM tbl_quotation
            WHERE AssignedJobID = %s   
        """
        cursor.execute(query, (jocardID,))

        # Update jobcard status to Ready for Pickup
        cursor.execute(
            "UPDATE tbl_jobcarddetails SET Status = 'Ready for Pickup' WHERE ID = %s",
            (jocardID,),
        )

__all__ = [
    'getDuplicateQuotationEntries',
    'displayDuplicateQuotationEntries',
    'deleteDuplicateQuotationEntry',
    'getQuotationJobCardDetails',
    'saveQuotationPartsAndServices',
    'save_quotation_parts_and_services_batch',
    'get_quote_details_by_job_id',
    'get_quote_confirmation_details_by_job_id',
    'get_interimandquotation_total_by_job_id',
    'get_defects_list_details_by_job_id',
    'get_priced_defects_list_details_by_job_id',
    'getDepositPaidOnQuotesAndPendingInvoices',
    'fillQuotationInvoiceData',
    'createQuotationInvoicePdf',
    'deleteFile',
    'populate_confirmation_from_quote',
    'saveFullQuotationPartsAndServicesFeedback',
    'updateQuotationPartsAndServices',
    'getClientQuotationFeedback',
    'getQuotationConfirmationFeedback',
    'saveJobCardDetailsFromInterimQuotation',
    'saveInterimQuotationPartsAndServices',
    'getInterimQuoteAndAmendedInvoiceStaff',
    'getPreviousInterimQuoteDetails',
    'getInterimQuote',
    'transitionInterimQuoteToInvoice',
]

from . import BMALocal as _compatibility_facade
