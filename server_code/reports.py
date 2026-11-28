from ._common import *

# *************************************************** Export To Excel Section ************************************
@anvil.server.callable()
def make_excel(headers, rows, filename="report.xlsx", sheet_name="Data"):
    """
    Generic Excel export utility.

    :param headers: list[str] - Header titles in order
    :param rows: list[list] or list[dict] - Data rows
    :param filename: str - Filename for download
    :param sheet_name: str - Sheet name
    :return: anvil.BlobMedia
    """
    _get_current_user()
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Add headers
    ws.append(headers)
    header_fill = PatternFill(
        start_color="D9E1F2", end_color="D9E1F2", fill_type="solid"
    )
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = header_fill

    # Add rows
    for row in rows:
        if isinstance(row, dict):
            values = [row.get(h, "") for h in headers]
        else:
            values = row
        ws.append(values)

    # Auto-fit column widths
    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                val = str(cell.value) if cell.value is not None else ""
                max_length = max(max_length, len(val))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = max_length + 2

    # Freeze header row + enable auto filter
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    # Save to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return anvil.BlobMedia(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        buffer.read(),
        name=filename,
    )


@anvil.server.callable()
def export_assigned_jobcards(rows):
    _get_current_user()
    headers = [
        "No",
        "ReceivedDate",
        "JobCardRef",
        "Technician",
        "InvoicedAmount",
        "LabourAmount",
        "MakeAndModel",
    ]

    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append(
            {
                "No": i,
                "ReceivedDate": row.get("ReceivedDate", ""),
                "JobCardRef": row.get("JobCardRef", ""),
                "Technician": row.get("Technician", ""),
                "InvoicedAmount": row.get("InvoicedAmount", ""),
                "LabourAmount": row.get("LabourAmount", ""),
                "MakeAndModel": row.get("MakeAndModel", ""),
            }
        )
    return make_excel(
        headers,
        processed_rows,
        filename="assigned_jobcards.xlsx",
        sheet_name="Jobcards",
    )


@anvil.server.callable()
def export_missing_buying_prices(rows):
    _get_current_user()
    headers = ["No", "Supplier", "Name", "PartNo", "BuyingPrice"]

    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append(
            {
                "No": i,
                "Supplier": row.get("Supplier", ""),
                "Name": row.get("Name", ""),
                "PartNo": row.get("PartNo", ""),
                "BuyingPrice": row.get("BuyingPrice", ""),
            }
        )

    return make_excel(
        headers,
        processed_rows,
        filename="missing_buying_prices.xlsx",
        sheet_name="Buying Prices",
    )


@anvil.server.callable()
def export_missing_selling_prices(rows):
    _get_current_user()
    headers = ["No", "Supplier", "Name", "PartNo", "SellingPrice", "DiscountPrice"]

    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append(
            {
                "No": i,
                "Supplier": row.get("Supplier", ""),
                "Name": row.get("Name", ""),
                "PartNo": row.get("PartNo", ""),
                "SellingPrice": row.get("Amount", ""),
                "DiscountPrice": row.get("Discount", ""),
            }
        )

    return make_excel(
        headers,
        processed_rows,
        filename="missing_selling_prices.xlsx",
        sheet_name="Selling Prices",
    )


@anvil.server.callable()
def export_client_payment_details(rows):
    _get_current_user()
    headers = [
        "No",
        "JobReceivedDate",
        "JobCardRef",
        "Fullname",
        "Phone",
        "TotalPaid",
        "Discount",
        "Balance",
    ]

    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append(
            {
                "No": i,
                "JobReceivedDate": row.get("JobReceivedDate", ""),
                "JobCardRef": row.get("JobCardRef", ""),
                "Fullname": row.get("Fullname", ""),
                "Phone": row.get("Phone", ""),
                "TotalPaid": row.get("TotalPaid", 0),
                "Discount": row.get("Discount", 0),
                "Balance": row.get("Balance", 0),
            }
        )

    return make_excel(
        headers,
        processed_rows,
        filename="client_payment_details.xlsx",
        sheet_name="Client Payments",
    )


@anvil.server.callable()
def export_stock_balance(rows):
    _get_current_user()
    headers = [
        "No",
        "Name",
        "PartNo",
        "Reorder Level",
        "Total Stock",
        "Total Issued",
        "Variance",
        "Stock Balance",
        "Below Reorder Level",
    ]

    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append(
            {
                "No": i,
                "Name": row.get("Name", ""),
                "PartNo": row.get("PartNo", ""),
                "Reorder Level": row.get("OrderLevel", ""),
                "Total Stock": row.get("TotalStock", ""),
                "Total Issued": row.get("TotalIssued", ""),
                "Variance": row.get("LatestStockTake", ""),
                "Stock Balance": row.get("StockBalance", ""),
                "Below Reorder Level": row.get("BelowOrderLevel", ""),
            }
        )
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    return make_excel(
        headers,
        processed_rows,
        filename=f"export_stock_balance_{today}.xlsx",
        sheet_name="Stock Balance",
    )


@anvil.server.callable()
def export_monthly_schedule(rows):
    _get_current_user()
    headers = [
        "No",
        "Date",
        "Name",
        "Total Amount",
        "Car Parts",
        "Engine Oil",
        "Consumable",
        "Diagnosis",
        "Labour",
        "Engine Wash",
        "Alignment",
        "T/Gearbox Oil",
        "Others",
        "Discount",
        "Balance",
    ]

    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append(
            {
                "No": i,
                "Date": row.get("Date", ""),
                "Name": row.get("ClientName", ""),
                "Total Amount": row.get("TotalInvoiceAmount", ""),
                "Car Parts": row.get("CarParts", ""),
                "Engine Oil": row.get("EngineOil", ""),
                "Consumable": row.get("Consumable", ""),
                "Diagnosis": row.get("Diagnosis", ""),
                "Labour": row.get("Labour", ""),
                "Engine Wash": row.get("EngineWash", ""),
                "Alignment": row.get("Alignment", ""),
                "T/Gearbox Oil": row.get("TransferGearboxOil", ""),
                "Others": row.get("Others", ""),
                "Discount": row.get("TotalDiscount", ""),
                "Balance": row.get("Balance", ""),
            }
        )

    return make_excel(
        headers,
        processed_rows,
        filename="export_monthly_schedule.xlsx",
        sheet_name="Monthly Schedule",
    )

@anvil.server.callable()
def export_current_selling_prices_and_reorder_levels():
    _get_current_user()
    headers = ["No", "Name", "PartNo", "OrderLevel", "SellingPrice", "DiscountPrice"]

    # Execute the SQL query
    with db_cursor() as cursor:
        query = """
            SELECT 
                tbl_carpartnames.Name, 
                tbl_carpartnames.PartNo, 
                tbl_carpartnames.OrderLevel,
                tbl_partssellingprice.Amount, 
                tbl_partssellingprice.SaleDiscount  
            FROM tbl_carpartnames 
            INNER JOIN tbl_partssellingprice 
                ON tbl_carpartnames.ID = tbl_partssellingprice.CarPartsNamesID
            ORDER BY tbl_carpartnames.Name ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

    # Transform into list-of-dicts
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append(
            {
                "No": i,
                "Name": row[0],
                "PartNo": row[1],
                "OrderLevel": row[2],
                "SellingPrice": row[3],
                "DiscountPrice": row[4],
            }
        )

    return make_excel(
        headers,
        processed_rows,
        filename="selling_prices_and_reorder_levels.xlsx",
        sheet_name="Selling Prices & Reorder Lvl",
    )

@anvil.server.callable()
def export_current_parts_and_partno():
    _get_current_user()
    headers = ["No", "Name", "PartNo", "Quantity"]

    # Execute the SQL query
    with db_cursor() as cursor:
        query = """
            SELECT 
                tbl_carpartnames.Name, 
                tbl_carpartnames.PartNo
            FROM tbl_carpartnames 
            ORDER BY tbl_carpartnames.Name ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

    # Transform into list-of-dicts
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append(
            {
                "No": i,
                "Name": row[0],
                "PartNo": row[1],
                "Quantity": "",
            }
        )

    return make_excel(
        headers,
        processed_rows,
        filename="current_parts_and_partno.xlsx",
        sheet_name="Current Parts & PartNo",
    )

@anvil.server.callable()
def export_import_orders(rows):
    _get_current_user()
    
    # Sort rows by OrderDate in descending order
    sorted_rows = sorted(
        rows, 
        key=lambda row: row.get("OrderDate", ""), 
        reverse=True
    )
    
    headers = [
        "No",
        "Date",
        "Client",
        "Name",
        "PartNo",
        "Quantity",
        "Brand",
        "Status"
    ]

    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(sorted_rows, start=1):
        processed_rows.append(
            {
                "No": i,
                "Date": row.get("OrderDate", ""),
                "Client": row.get("Client", ""),
                "Name": row.get("Name", ""),
                "PartNo": row.get("Part_No", ""),
                "Quantity": row.get("Quantity", ""),
                "Brand": row.get("Brand", ""),
                "Status": row.get("Status", ""),
            }
        )
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    return make_excel(
        headers,
        processed_rows,
        filename=f"export_import_orders_{today}.xlsx",
        sheet_name="Import Orders",
    )


# *************************************************** Import From Excel Section ************************************

@anvil.server.callable()
def import_selling_prices_and_reorder_levels(file):
    _get_current_user()
    
    # Load the uploaded Excel file from Anvil media object
    from openpyxl import load_workbook
    file_bytes = BytesIO(file.get_bytes())
    wb = load_workbook(file_bytes, data_only=True)
    ws = wb.active

    # Validate headers
    expected_headers = ["No", "Name", "PartNo", "OrderLevel", "SellingPrice", "DiscountPrice"]
    actual_headers = [cell.value for cell in ws[1]]
    if actual_headers != expected_headers:
        raise Exception(
            f"Invalid file format. Expected headers: {expected_headers}, but got: {actual_headers}"
        )

    def is_valid_number(value):
        """Check if value is a non-negative number."""
        if value is None:
            return False, "missing"
        try:
            num = float(value)
            if isinstance(value, str) and value.strip().replace('.', '', 1).lstrip('-').isdigit() is False:
                return False, "not a number"
            if num < 0:
                return False, "negative"
            return True, num
        except (ValueError, TypeError):
            return False, "not a number"

    updated_count = 0
    skipped_rows = []

    with db_cursor() as cursor:
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            no, name, part_no, order_level, selling_price, discount_price = row

            # Skip completely empty rows
            if all(v is None for v in row):
                continue

            # Validate required fields
            if not name or not part_no:
                skipped_rows.append(f"Row {row_idx}: Missing Name or PartNo — skipped.")
                continue

            # Validate OrderLevel
            valid, order_level_result = is_valid_number(order_level)
            if not valid:
                if order_level_result == "negative":
                    skipped_rows.append(f"Row {row_idx} ({name}): OrderLevel cannot be negative ({order_level}) — skipped.")
                elif order_level_result == "not a number":
                    skipped_rows.append(f"Row {row_idx} ({name}): OrderLevel must be a number, got '{order_level}' — skipped.")
                else:
                    skipped_rows.append(f"Row {row_idx} ({name}): OrderLevel is missing — skipped.")
                continue

            # Validate SellingPrice
            valid, selling_price_result = is_valid_number(selling_price)
            if not valid:
                if selling_price_result == "negative":
                    skipped_rows.append(f"Row {row_idx} ({name}): SellingPrice cannot be negative ({selling_price}) — skipped.")
                elif selling_price_result == "not a number":
                    skipped_rows.append(f"Row {row_idx} ({name}): SellingPrice must be a number, got '{selling_price}' — skipped.")
                else:
                    skipped_rows.append(f"Row {row_idx} ({name}): SellingPrice is missing — skipped.")
                continue

            # Validate DiscountPrice (optional but must be non-negative number if present)
            if discount_price is not None:
                valid, discount_price_result = is_valid_number(discount_price)
                if not valid:
                    if discount_price_result == "negative":
                        skipped_rows.append(f"Row {row_idx} ({name}): DiscountPrice cannot be negative ({discount_price}) — skipped.")
                    elif discount_price_result == "not a number":
                        skipped_rows.append(f"Row {row_idx} ({name}): DiscountPrice must be a number, got '{discount_price}' — skipped.")
                    continue
            else:
                discount_price_result = 0.0

            # Fetch the CarPartNames ID using Name and PartNo
            cursor.execute("""
                SELECT ID FROM tbl_carpartnames
                WHERE Name = %s AND PartNo = %s
                LIMIT 1
            """, (str(name).strip(), str(part_no).strip()))
            part_row = cursor.fetchone()

            if not part_row:
                skipped_rows.append(f"Row {row_idx} ({name} / {part_no}): No matching part found in database — skipped.")
                continue

            car_part_id = part_row[0]

            # Update OrderLevel in tbl_carpartnames
            cursor.execute("""
                UPDATE tbl_carpartnames
                SET OrderLevel = %s
                WHERE ID = %s
            """, (int(order_level_result), car_part_id))

            # Update Amount and SaleDiscount in tbl_partssellingprice
            cursor.execute("""
                UPDATE tbl_partssellingprice
                SET Amount = %s, SaleDiscount = %s, SetPriceDate = %s
                WHERE CarPartsNamesID = %s
            """, (
                float(selling_price_result),
                float(discount_price_result),
                datetime.date.today(),
                car_part_id
            ))

            updated_count += 1

    # Build result summary
    summary = f"{updated_count} part(s) updated successfully."
    if skipped_rows:
        summary += f"\n{len(skipped_rows)} row(s) skipped:\n" + "\n".join(skipped_rows)

    return summary



# *************************************************** Download Job Card Report Section ************************************



@anvil.server.callable()
def get_jobcard_details(jobCardID):
    """Fetch full job card details for a given JobCardID."""
    _get_current_user()

    with db_cursor() as cursor:
        query = """
            SELECT
                tbl_jobcarddetails.ID,
                tbl_clientcontacts.Fullname AS ClientName,
                tbl_clientcontacts.Phone,
                tbl_clientcontacts.Address,
                tbl_clientcontacts.Email,
                tbl_technicians.Fullname AS TechnicianName,
                tbl_jobcarddetails.JobCardRef,
                tbl_jobcarddetails.ReceivedDate,
                tbl_jobcarddetails.DueDate,
                tbl_jobcarddetails.ExpDate,
                tbl_checkstaff.Staff,
                tbl_jobcarddetails.Ins,
                tbl_jobcarddetails.Comp,
                tbl_jobcarddetails.TPO,
                tbl_jobcarddetails.Spare,
                tbl_jobcarddetails.Jack,
                tbl_jobcarddetails.Brace,
                tbl_jobcarddetails.OtherItems,
                tbl_jobcarddetails.RegNo,
                tbl_jobcarddetails.MakeAndModel,
                tbl_jobcarddetails.ChassisNo,
                tbl_jobcarddetails.EngineCC,
                tbl_jobcarddetails.Mileage,
                tbl_jobcarddetails.EngineNo,
                tbl_jobcarddetails.EngineCode,
                tbl_jobcarddetails.Manual,
                tbl_jobcarddetails.Auto,
                tbl_jobcarddetails.Empty,
                tbl_jobcarddetails.Quarter,
                tbl_jobcarddetails.Half,
                tbl_jobcarddetails.ThreeQuarter,
                tbl_jobcarddetails.Full,
                tbl_jobcarddetails.PaintCode,
                tbl_jobcarddetails.ClientInstruction,
                tbl_jobcarddetails.Notes
            FROM
                tbl_technicians
            INNER JOIN(
                tbl_pendingassignedjobs
                INNER JOIN(
                    tbl_checkstaff
                    INNER JOIN(
                        tbl_clientcontacts
                        INNER JOIN tbl_jobcarddetails
                        ON tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails
                    )
                    ON tbl_checkstaff.ID = tbl_jobcarddetails.CheckedInBy
                )
                ON tbl_pendingassignedjobs.JobCardRefID = tbl_jobcarddetails.ID
            )
            ON tbl_technicians.ID = tbl_pendingassignedjobs.TechnicianID
            WHERE tbl_jobcarddetails.ID = %s
        """

        cursor.execute(query, (jobCardID,))
        row = cursor.fetchone()

    if not row:
        return []

    # Client instructions (index 33)
    raw_instruction = row[33] or ""

    # Convert HTML block/list boundaries into newlines
    text_with_breaks = re.sub(
        r'</(p|li|div|br)\s*>',
        '\n',
        raw_instruction,
        flags=re.IGNORECASE
    )

    text_with_breaks = re.sub(
        r'<br\s*/?>',
        '\n',
        text_with_breaks,
        flags=re.IGNORECASE
    )

    # Remove remaining HTML tags
    text_only = re.sub(r'<[^>]+>', '', text_with_breaks)

    lines = [
        line.strip()
        for line in text_only.splitlines()
        if line.strip()
    ]

    formatted_instruction = "\n".join(lines)

    # Map tuple to dictionary
    result = {
        "JobCardId": row[0],
        "ClientName": str(row[1]) if row[1] else "",
        "ClientPhone": str(row[2]) if row[2] else "",
        "ClientAddress": str(row[3]) if row[3] else "",
        "ClientEmail": str(row[4]) if row[4] else "",
        "TechnicianName": str(row[5]) if row[5] else "",
        "JobCardRef": str(row[6]) if row[6] else "",
        "ReceivedDate": str(row[7]) if row[7] else "",
        "DueDate": str(row[8]) if row[8] else "",
        "ExpDate": str(row[9]) if row[9] else "",
        "CheckedInBy": str(row[10]) if row[10] else "",
        "Ins": str(row[11]) if row[11] else "",
        "Comp": str(row[12]) if row[12] else "",
        "TPO": str(row[13]) if row[13] else "",
        "Spare": str(row[14]) if row[14] else "",
        "Jack": str(row[15]) if row[15] else "",
        "Brace": str(row[16]) if row[16] else "",
        "OtherItems": str(row[17]) if row[17] else "",
        "RegNo": str(row[18]) if row[18] else "",
        "MakeAndModel": str(row[19]) if row[19] else "",
        "ChassisNo": str(row[20]) if row[20] else "",
        "EngineCC": str(row[21]) if row[21] else "",
        "Mileage": str(row[22]) if row[22] else "",
        "EngineNo": str(row[23]) if row[23] else "",
        "EngineCode": str(row[24]) if row[24] else "",
        "Manual": str(row[25]) if row[25] else "",
        "Auto": str(row[26]) if row[26] else "",
        "Empty": str(row[27]) if row[27] else "",
        "Quarter": str(row[28]) if row[28] else "",
        "Half": str(row[29]) if row[29] else "",
        "ThreeQuarter": str(row[30]) if row[30] else "",
        "Full": str(row[31]) if row[31] else "",
        "PaintCode": str(row[32]) if row[32] else "",
        "ClientInstruction": formatted_instruction,
        "Notes": str(row[34]) if row[34] else "",
    }

    return result



@anvil.server.callable()
def get_signature(jobCardID: int) -> str | None:
    """
    Fetch the Base64-encoded client signature for a given job card.
    Returns None if no signature is found.
    """
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Signature
            FROM tbl_signedjobcards
            WHERE AssignedJobID = %s
            ORDER BY ID DESC
            LIMIT 1
        """
        cursor.execute(query, (jobCardID,))
        row = cursor.fetchone()

    if row:
        # If Signature is stored as BLOB → convert to base64
        if isinstance(row[0], (bytes, bytearray)):
            return base64.b64encode(row[0]).decode("utf-8")
        # If already base64/text stored in DB → return as is
        return row[0]

    return None

@anvil.server.callable()
def get_createdAt(jobCardID: int) -> str | None:
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT CreatedAt
            FROM tbl_signedjobcards
            WHERE AssignedJobID = %s
            ORDER BY ID DESC
            LIMIT 1
        """
        cursor.execute(query, (jobCardID,))
        row = cursor.fetchone()

    if row and row[0]:
        return row[0].strftime("%d-%m-%Y")

    return None


@anvil.server.callable()
def fillJobCardReport(jobCardID, logo_path: str = os.getenv("LOGO"),font_path: str = os.getenv("FONT_PATH")) -> str:
    _get_current_user()
    data = get_jobcard_details(jobCardID)

    signature_b64 = get_signature(jobCardID)
    if signature_b64:
        signature_html = f"""
                <img src="data:image/png;base64,{signature_b64}" 
                     alt="Client Signature" 
                     style="max-width: 90%; height: auto; display: block; border: 1px solid #ccc; padding: 4px;"/>
                """
    else:
        signature_html = "<em>No signature available</em>"

    createdAt = get_createdAt(jobCardID)

    docTitle = "Jobcard Details"

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

    insurance_html = ""
    if data["Comp"]:
        insurance_html += "Comprehensive"
    if data["TPO"]:
        insurance_html += "Third Party Only"

    items_list = []
    if data["Spare"]:
        items_list.append("Spare")
    if data["Jack"]:
        items_list.append("Jack")
    if data["Brace"]:
        items_list.append("Brace")

    # NEW: turn the newline-joined OtherItems into an HTML list
    OtherItems_lines = [line for line in (data["OtherItems"] or "").split("\n") if line.strip()]
    if OtherItems_lines:
        OtherItems_html = (
            "<ul style='margin:0; padding-left:16px;'>"
            + "".join(f"<li>{line}</li>" for line in OtherItems_lines)
            + "</ul>"
        )
    else:
        OtherItems_html = "None"

    
    transmission_html = []
    if data["Manual"]:
        transmission_html.append("Manual")
    if data["Auto"]:
        transmission_html.append("Auto")

    tank_html = []
    if data["Empty"]:
        tank_html.append("Empty")
    if data["Quarter"]:
        tank_html.append("1/4")
    if data["Half"]:
        tank_html.append("1/2")
    if data["ThreeQuarter"]:
        tank_html.append("3/4")
    if data["Full"]:
        tank_html.append("Full")

    # NEW: turn the newline-joined ClientInstruction into an HTML list
    instruction_lines = [line for line in (data["ClientInstruction"] or "").split("\n") if line.strip()]
    if instruction_lines:
        instruction_html = (
            "<ul style='margin:0; padding-left:16px;'>"
            + "".join(f"<li>{line}</li>" for line in instruction_lines)
            + "</ul>"
        )
    else:
        instruction_html = "None"

    html_content = f"""
    <!DOCTYPE html>
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
        @page {{
          size: A4;
          margin: 20mm;
        }}
        body {{
          font-family: Roboto, Noto, Arial, sans-serif;
          font-size: 12pt;
          line-height: 1.5;
          background: #fff;
          margin: 0;
          color: #000;
        }}
        .container {{
          width: 100%;
          margin: auto;
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
        .doc-title {{
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
          text-transform: uppercase;
          font-family: 'Mozilla Headline';
        }}
        .section-title {{
          font-size: 12pt;
          font-weight: bold;
          border-bottom: 1px solid #000;
          margin: 16px 0 8px;
          padding-bottom: 3px;
        }}
        .detail-row {{
            display: grid;
            grid-template-columns: 120px 1fr; /* Slightly smaller label column for 3-col layout */
            column-gap: 8px;
            margin-bottom: 12px;
            padding: 6px 10px;
            border: 1px solid #eee; /* subtle separation */
            border-radius: 4px;
            background: #fafafa;
        }}
        .detail-label {{
            font-weight: bold;
            font-size: 12px; /* Slightly smaller for 3-col layout */
            color: rgba(0,0,0,0.87);
            font-family: 'Mozilla Headline';      
        }}
        .detail-value {{
            font-size: 12px; /* Slightly smaller for 3-col layout */
            color: rgba(0,0,0,0.87);
            text-align: left;   
        }}        
        .signature {{
          margin-top: 20px;
          padding: 10px;
          text-align: left;
          page-break-inside: avoid;
          font-family: 'Mozilla Headline';
        }}
        
        .terms-conditions {{
            margin-top: 18px;
            padding: 10px 12px;
            border: 1px solid #000;
            page-break-inside: avoid;
            font-family: Roboto, Noto, Arial, sans-serif;
            font-size: 9pt;
            line-height: 1.35;
            color: #000;
        }}

        .terms-title {{
            font-family: 'Mozilla Headline';
            font-size: 11pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 8px;
            text-transform: uppercase;
        }}

        .terms-conditions p {{
            margin: 0 0 6px 0;
            text-align: justify;
        }}

        .terms-conditions .acceptance {{
            margin-top: 10px;
            font-weight: bold;
        }}
        footer {{
          text-align: center;
          font-size: 10pt;
          color: #444;
          margin-top: 5px;
          padding-top: 2px;
          border-top: 1px solid #000;
          page-break-inside: avoid;
          font-family: 'Mozilla Headline';
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="logo-section">
            <div class="logo-container">
                <div class="logo-image">
                    {logo_img_tag}
                </div>
            </div>
        </div>
        <div class="doc-title">{docTitle}</div>


        <!-- UPDATED: Changed to 3-column table layout -->
        <table style="width: 100%; table-layout: fixed; margin: 24px 0;">
            <tr>
                <!-- First Column - Client Details -->
                <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Name:</span>
                        <div>
                        <span class="detail-value">{data['ClientName']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Phone:</span>
                        <div>
                        <span class="detail-value">{data['ClientPhone']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Address:</span>
                        <div>
                        <span class="detail-value">{data['ClientAddress']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Email:</span>
                        <div>
                        <span class="detail-value">{data['ClientEmail']}</span>
                        </div>
                    </div>
                </td>

                <!-- Second Column - Vehicle Basic Details -->
                <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Reg No:</span>
                        <div>
                        <span class="detail-value">{data['RegNo']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Make & Model:</span>
                        <div>
                        <span class="detail-value">{data['MakeAndModel']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Chassis No:</span>
                        <div>
                        <span class="detail-value">{data['ChassisNo']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Engine CC:</span>
                        <div>
                        <span class="detail-value">{data['EngineCC'] if data['EngineCC'] else "Not Captured"}</span>
                        </div>
                    </div>
                </td>

                <!-- Third Column - Vehicle Technical Details -->
                <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Mileage:</span>
                        <div>
                        <span class="detail-value">{data['Mileage']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Engine No:</span>
                        <div>
                        <span class="detail-value">{data['EngineNo'] if data['EngineNo'] else "Not Captured"}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Engine Code:</span>
                        <div>
                        <span class="detail-value">{data['EngineCode'] if data['EngineCode'] else "Not Captured"}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Paint Code:</span>
                        <div>
                        <span class="detail-value">{data['PaintCode'] if data['PaintCode'] else "Not Captured"}</span>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
        <!-- END UPDATED -->

        
        <!-- UPDATED: Changed to 3-column table layout -->
        <table style="width: 100%; table-layout: fixed; margin: 24px 0;">
            <tr>
                <div class="section-title" style="margin-top: 5px;"></div>
                <!-- First Column  -->
                <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Ref:</span>
                        <div>
                        <span class="detail-value">{data['JobCardRef']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Received:</span>
                        <div>
                        <span class="detail-value">{data['ReceivedDate']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Due:</span>
                        <div>
                        <span class="detail-value">{data['DueDate']}</span>
                        </div>
                    </div>
                </td>

                <!-- Second Column  -->
                <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Insurance Expiry:</span>
                        <div>
                        <span class="detail-value">{data['ExpDate'] if data['ExpDate'] else "Not Captured"}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Checked In By:</span>
                        <div>
                        <span class="detail-value">{data['CheckedInBy']}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Insurance:</span>
                        <div>
                        <span class="detail-value">{insurance_html}</span>
                        </div>
                    </div>
                </td>

                <!-- Third Column -->
                <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Available Items:</span>
                        <div>
                        <span class="detail-value">{", ".join(items_list) if items_list else "No Spare/Jack/Brace"}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Transmission:</span>
                        <div>
                        <span class="detail-value">{",".join(transmission_html) if transmission_html else "Not specified"}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Tank Level:</span>
                        <div>
                        <span class="detail-value">{",".join(tank_html) if tank_html else "Not specified"}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">OtherItems:</span>
                        <div>
                        <span class="detail-value">{OtherItems_html}</span>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
        <!-- END UPDATED -->

        <!-- UPDATED: Changed to 3-column table layout -->
        <table style="width: 100%; table-layout: fixed; margin: 24px 0;">
            <tr>
                <div class="section-title" style="margin-top: 2px;"></div>
                <!-- First Column -->
                <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Instructions:</span>
                        <div>
                        <span class="detail-value">{instruction_html}</span>
                        </div>
                    </div>
                </td>

                <!-- Second Column -->
                <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Tech Notes:</span>
                        <div>
                        <span class="detail-value">{data['Notes'] if data['Notes'] else "None"}</span>
                        </div>
                    </div>
                </td>

                <!-- Third Column -->
                <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Technician:</span>
                        <div>
                        <span class="detail-value">{data['TechnicianName']}</span>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
        <!-- END UPDATED -->

        <!-- TERMS & CONDITIONS -->
        <div class="terms-conditions">
            <div class="terms-title">Terms & Conditions</div>

            <p>
                <strong>(A)</strong> Vehicles are driven &amp; stored at owner's risk and the owner must ensure
                that they are adequately insured while in custody or in control of a member of the motor trade
                for the purpose of repair or upkeep.
            </p>

            <p>
                <strong>(B)</strong> I agree to pay for all work and parts required for the repairs described
                above at your retail charge. It is understood that any estimate given is provisional and all
                repairs are undertaken on a cash basis unless prior arrangements for credit have been approved.
                Any additional work found to be necessary must be authorised by myself prior to commencement.
                All goods shall remain the property of the seller until paid for in full.
            </p>

            <p>
                <strong>(C)</strong> Vehicles uncollected within 7 days after completion of instructions or issue
                of quotation will attract storage charges of Kes. 500 per day. If not collected after three
                months, vehicles shall be sold under disposal of unclaimed goods act to defray the company's cost.
            </p>

            <p>
                <strong>(D)</strong> Any claim / complaint in respect of work done as per the owner's instructions
                shall be notified to the company in writing within seven days after vehicle or goods delivery
                to the owner or after such reason for complaint has come to the knowledge of the owner whichever
                will be sooner and any claim not so notified shall be deemed waived.
            </p>

            <p class="acceptance">
                I hereby authorise and accept your terms and conditions. Nothing herein is designed to nor will
                it affect a customer's statutory rights.
            </p>
        </div>

        <!-- SIGNATURE & DATE -->
        <table style="width: 100%; table-layout: fixed; margin: 24px 0;">
            <tr>
                <div class="section-title" style="margin-top: 5px;"></div>

                <!-- Signature Column -->
                <td style="width: 70%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Signature:</span>
                        <div>
                            <span class="detail-value">{signature_html}</span>
                        </div>
                    </div>
                </td>

                <!-- Date Column -->
                <td style="width: 30%; vertical-align: top; padding: 0 16px;">
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <div>
                            <span class="detail-value">
                                {createdAt if createdAt else "Not Captured"}
                            </span>
                        </div>
                    </div>
                </td>

            </tr>
        </table>
        <!-- END SIGNATURE & DATE -->

        <footer>
          Joy Is The Feeling Of Being Looked After By The Best - BMW CENTER For Your BMW.
        </footer>
      </div>
    </body>
    </html>
    """
    return html_content


@anvil.server.callable()
def createSignedJobcardPdf(jobCardID):
    _get_current_user()
    try:
        docName = getJobCardRef(jobCardID)
        fileName = str(docName[0]["JobCardRef"]) + " Jobcard"

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

        html_string = fillJobCardReport(jobCardID)
        get_pdfkit().from_string(
            html_string, fileName, options=setting_options, configuration=get_pdfkit_config()
        )
        media_object = anvil.media.from_file(fileName, "application/pdf", name=fileName)
        return media_object

    except Exception as e:
        print("PDF generation failed:", str(e))
        raise

@anvil.server.callable()
def get_reports_bootstrap(sections=None):
    """
    Single-RPC, single-cursor bootstrap for initial read-only Report datasets.

    Args:
        sections (list[str] | tuple[str] | set[str] | None): Optional subset of
            {"clients", "car_details", "technicians", "staffs", "inventory",
             "quote_invoice", "payments"}. Defaults to all sections when None.
    Returns:
        dict: Bundled initial datasets keyed by report target.
    """
    _get_current_user()
    allowed_sections = {
        "clients",
        "car_details",
        "technicians",
        "staffs",
        "inventory",
        "quote_invoice",
        "payments",
    }
    if sections is None:
        wanted = allowed_sections
    elif isinstance(sections, (list, tuple, set)):
        wanted = set()
        for sec in sections:
            if not isinstance(sec, str) or sec not in allowed_sections:
                raise ValueError(f"Invalid report bootstrap section: {sec!r}")
            wanted.add(sec)
    else:
        raise ValueError("sections must be a list of valid section names or None.")

    if not wanted:
        return {}

    bundle = {}
    with db_cursor() as cursor:
        if "clients" in wanted:
            cursor.execute(
                "SELECT ID, Fullname, Phone, Address, Email, Narration "
                "FROM tbl_clientcontacts "
                "ORDER BY Fullname ASC"
            )
            bundle["clients"] = [
                {
                    "No": idx,
                    "ID": r[0],
                    "Fullname": r[1],
                    "Phone": r[2],
                    "Address": r[3],
                    "Email": r[4],
                    "Narration": r[5],
                }
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]

        if "car_details" in wanted:
            cursor.execute(
                """
                SELECT
                    c.Fullname,
                    c.Phone,
                    j.RegNo,
                    j.ChassisNo,
                    j.ReceivedDate,
                    j.JobCardRef,
                    j.MakeAndModel
                FROM tbl_clientcontacts c
                INNER JOIN tbl_jobcarddetails j ON c.ID = j.ClientDetails
                ORDER BY j.ReceivedDate DESC
                LIMIT %s
                """,
                (200,),
            )
            bundle["car_details"] = [
                {
                    "No": idx,
                    "Fullname": r[0],
                    "Phone": r[1],
                    "RegNo": r[2],
                    "ChassisNo": r[3],
                    "ReceivedDate": r[4],
                    "JobCardRef": r[5],
                    "MakeAndModel": r[6],
                }
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]

        if "technicians" in wanted:
            cursor.execute(
                """
                SELECT tbl_technicians.ID, tbl_technicians.Fullname, tbl_technicians.Phone,
                       tbl_toolkits.ToolkitName, tbl_technicians.IsArchived
                FROM tbl_technicians
                INNER JOIN tbl_toolkits ON tbl_technicians.ToolkitID = tbl_toolkits.ID
                ORDER BY Fullname ASC
                """
            )
            bundle["technicians_report"] = [
                {
                    "No": idx,
                    "ID": r[0],
                    "Fullname": r[1],
                    "Phone": r[2],
                    "Toolkit": r[3],
                    "IsArchived": "Yes" if r[4] == 1 else "No",
                }
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]

            cursor.execute(
                """
                SELECT
                    jd.ReceivedDate,
                    jd.JobCardRef,
                    t.Fullname,
                    SUM(
                        CASE
                            WHEN i.QuantityIssued IS NULL THEN i.Amount
                            ELSE i.Amount * i.QuantityIssued
                        END
                    ) AS InvoicedAmount,
                    MAX(
                        CASE
                            WHEN i.Item LIKE '%Labour%' THEN i.Amount
                            ELSE 0
                        END
                    ) AS LabourAmount,
                    jd.MakeAndModel
                FROM tbl_invoices AS i
                INNER JOIN tbl_jobcarddetails AS jd ON i.AssignedJobID = jd.ID
                INNER JOIN tbl_pendingassignedjobs AS pj ON jd.ID = pj.JobCardRefID
                INNER JOIN tbl_technicians AS t ON t.ID = pj.TechnicianID
                GROUP BY jd.ReceivedDate, jd.JobCardRef, t.Fullname, jd.MakeAndModel
                ORDER BY jd.ReceivedDate DESC
                """
            )
            assigned_jobs = [
                {
                    "No": idx,
                    "ReceivedDate": r[0],
                    "JobCardRef": r[1],
                    "Technician": r[2],
                    "InvoicedAmount": f"{float(r[3] or 0):,.2f}",
                    "LabourAmount": f"{float(r[4] or 0):,.2f}",
                    "MakeAndModel": r[5],
                }
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]
            cursor.execute(
                """
                SELECT ID, Fullname
                FROM tbl_technicians
                WHERE IsArchived = FALSE
                ORDER BY Fullname ASC
                """
            )
            active_techs = [(r[1], r[0]) for r in cursor.fetchall()]
            bundle["assigned_jobcards"] = {"jobs": assigned_jobs, "technicians": active_techs}

        if "staffs" in wanted:
            cursor.execute(
                "SELECT ID, Staff, Phone, IsArchived "
                "FROM tbl_checkstaff "
                "ORDER BY Staff ASC"
            )
            bundle["staffs_report"] = [
                {
                    "No": idx,
                    "ID": r[0],
                    "Fullname": r[1],
                    "Phone": r[2],
                    "Active": "Yes" if r[3] == 1 else "No",
                }
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]

        if "inventory" in wanted:
            cursor.execute(
                """
                WITH latest_stock AS (
                    SELECT sp.CarPart, sp.UnitCost, sp.Date,
                           ROW_NUMBER() OVER (PARTITION BY sp.CarPart ORDER BY sp.ID DESC) AS rn
                    FROM tbl_stockparts sp
                ),
                issued AS (
                    SELECT CarPartID, SUM(QuantityIssued) AS TotalIssued
                    FROM tbl_assignedcarparts
                    GROUP BY CarPartID
                ),
                latest_stocktake AS (
                    SELECT CarPartNameID, HarmornizedValue
                    FROM (
                        SELECT
                            CarPartNameID,
                            HarmornizedValue,
                            ROW_NUMBER() OVER (PARTITION BY CarPartNameID ORDER BY StockTakeDate DESC) AS rn
                        FROM tbl_stocktakeharmonized
                    ) ranked
                    WHERE rn = 1
                )
                SELECT
                    cpn.Name,
                    cpn.PartNo,
                    cpn.OrderLevel AS `Reorder Level`,
                    ls.UnitCost AS Cost,
                    psp.Amount AS Selling,
                    psp.SaleDiscount AS Discount,
                    MAX(sp.Date) AS MaxOfDate,
                    (COALESCE(SUM(sp.NoOfUnits), 0)
                        - COALESCE(i.TotalIssued, 0)
                        + COALESCE(lst.HarmornizedValue, 0)) AS StockBalance
                FROM tbl_carpartnames cpn
                INNER JOIN tbl_partssellingprice psp ON cpn.ID = psp.CarPartsNamesID
                INNER JOIN tbl_stockparts sp ON cpn.ID = sp.CarPart
                INNER JOIN latest_stock ls ON ls.CarPart = cpn.ID AND ls.rn = 1
                LEFT JOIN issued i ON cpn.ID = i.CarPartID
                LEFT JOIN latest_stocktake lst ON cpn.ID = lst.CarPartNameID
                GROUP BY
                    cpn.Name, cpn.PartNo, cpn.OrderLevel, psp.Amount, psp.SaleDiscount,
                    cpn.ID, ls.UnitCost, i.TotalIssued, lst.HarmornizedValue
                ORDER BY cpn.Name
                """
            )
            bundle["price_catalogue"] = [
                {
                    "No": idx,
                    "Name": r[0],
                    "PartNo": r[1],
                    "ReorderLevel": r[2],
                    "Cost": f"{float(r[3]):,.2f}" if r[3] is not None else None,
                    "Selling": f"{float(r[4]):,.2f}" if r[4] is not None else None,
                    "Discount": r[5],
                    "MaxOfDate": r[6],
                    "StockBalance": f"{float(r[7] or 0):.2f}",
                }
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]

            cursor.execute(
                """
                SELECT n.ID, n.Name, n.PartNo, l.Location
                FROM tbl_carpartnames n
                INNER JOIN tbl_carpartslocation l ON l.ID = n.Location
                ORDER BY n.Name
                """
            )
            bundle["stock_location"] = [
                {"No": idx, "Name": r[1], "PartNo": r[2], "Location": r[3]}
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]

            cursor.execute(
                """
                WITH issued AS (
                    SELECT CarPartID, SUM(QuantityIssued) AS TotalIssued
                    FROM tbl_assignedcarparts
                    GROUP BY CarPartID
                ),
                latest_stocktake AS (
                    SELECT CarPartNameID, HarmornizedValue
                    FROM (
                        SELECT
                            CarPartNameID,
                            HarmornizedValue,
                            ROW_NUMBER() OVER (PARTITION BY CarPartNameID ORDER BY StockTakeDate DESC) AS rn
                        FROM tbl_stocktakeharmonized
                    ) ranked
                    WHERE rn = 1
                )
                SELECT
                    cp.ID,
                    cp.Name,
                    cp.PartNo,
                    cp.OrderLevel,
                    COALESCE(i.TotalIssued, 0) AS TotalIssued,
                    COALESCE(l.HarmornizedValue, 0) AS LatestStockTake,
                    MAX(sp.Date) AS LastStockDate,
                    SUM(sp.NoOfUnits) AS TotalStock,
                    (COALESCE(SUM(sp.NoOfUnits), 0)
                        - COALESCE(i.TotalIssued, 0)
                        + COALESCE(l.HarmornizedValue, 0)) AS StockBalance,
                    CASE
                        WHEN (COALESCE(SUM(sp.NoOfUnits), 0)
                            - COALESCE(i.TotalIssued, 0)
                            + COALESCE(l.HarmornizedValue, 0)) < cp.OrderLevel
                        THEN 'Yes'
                        ELSE 'No'
                    END AS BelowOrderLevel
                FROM tbl_carpartnames cp
                LEFT JOIN tbl_stockparts sp ON cp.ID = sp.CarPart
                LEFT JOIN issued i ON cp.ID = i.CarPartID
                LEFT JOIN latest_stocktake l ON cp.ID = l.CarPartNameID
                GROUP BY cp.ID, cp.Name, cp.PartNo, cp.OrderLevel, i.TotalIssued, l.HarmornizedValue
                ORDER BY cp.Name
                """
            )
            bundle["stock_balance"] = [
                {
                    "No": idx,
                    "Name": r[1],
                    "PartNo": r[2],
                    "OrderLevel": r[3],
                    "TotalIssued": float(r[4] or 0),
                    "LatestStockTake": float(r[5] or 0),
                    "TotalStock": float(r[7] or 0),
                    "StockBalance": f"{float(r[8] or 0):.2f}",
                    "BelowOrderLevel": r[9],
                }
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]

        if "quote_invoice" in wanted:
            cursor.execute(
                """
                SELECT
                    j.ID AS ID,
                    j.ReceivedDate AS ReceivedDate,
                    j.JobCardRef AS JobCardRef,
                    COALESCE(q.QuotationTotal, 0) AS QuotationTotal,
                    COALESCE(i.InvoiceTotal, 0) AS InvoiceTotal
                FROM tbl_jobcarddetails j
                INNER JOIN (
                    SELECT AssignedJobID,
                           SUM(CASE WHEN QuantityIssued IS NULL THEN Amount ELSE QuantityIssued * Amount END) AS QuotationTotal
                    FROM tbl_quotation
                    GROUP BY AssignedJobID
                ) q ON q.AssignedJobID = j.ID
                INNER JOIN (
                    SELECT AssignedJobID,
                           SUM(CASE WHEN QuantityIssued IS NULL THEN Amount ELSE QuantityIssued * Amount END) AS InvoiceTotal
                    FROM tbl_invoices
                    GROUP BY AssignedJobID
                ) i ON i.AssignedJobID = j.ID
                ORDER BY j.ReceivedDate DESC
                """
            )
            bundle["quote_invoice_totals"] = [
                {
                    "No": idx,
                    "ID": r[0],
                    "ReceivedDate": r[1],
                    "JobCardRef": r[2],
                    "QuotationTotal": f"{float(r[3] or 0):,.2f}",
                    "InvoiceTotal": f"{float(r[4] or 0):,.2f}",
                }
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]

        if "payments" in wanted:
            cursor.execute(
                """
                SELECT
                    tbl_clientcontacts.Fullname,
                    tbl_clientcontacts.Phone,
                    tbl_jobcarddetails.JobCardRef,
                    tbl_jobcarddetails.ReceivedDate,
                    SUM(tbl_payments.AmountPaid) AS TotalPaid,
                    MAX(tbl_payments.Discount) AS Discount,
                    lp.Balance AS LatestBalance
                FROM tbl_payments
                INNER JOIN tbl_jobcarddetails ON tbl_jobcarddetails.ID = tbl_payments.JobCardRefID
                INNER JOIN tbl_clientcontacts ON tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails
                LEFT JOIN (
                    SELECT p1.JobCardRefID, p1.Balance
                    FROM tbl_payments p1
                    INNER JOIN (
                        SELECT JobCardRefID, MAX(ID) AS MaxID
                        FROM tbl_payments
                        GROUP BY JobCardRefID
                    ) pmax ON p1.ID = pmax.MaxID
                ) lp ON lp.JobCardRefID = tbl_jobcarddetails.ID
                GROUP BY tbl_clientcontacts.Fullname, tbl_clientcontacts.Phone,
                         tbl_jobcarddetails.JobCardRef, tbl_jobcarddetails.ReceivedDate,
                         tbl_jobcarddetails.ID, lp.Balance
                ORDER BY tbl_jobcarddetails.ReceivedDate DESC
                """
            )
            bundle["payment_summary"] = [
                {
                    "No": idx,
                    "JobReceivedDate": r[3].strftime("%Y-%m-%d") if r[3] else None,
                    "JobCardRef": r[2],
                    "Fullname": r[0],
                    "Phone": r[1],
                    "TotalPaid": f"{float(r[4] or 0):,.2f}",
                    "Discount": f"{float(r[5] or 0):,.2f}",
                    "Balance": f"{float(r[6] or 0):,.2f}",
                }
                for idx, r in enumerate(cursor.fetchall(), start=1)
            ]

    return bundle


__all__ = [
    'make_excel',
    'export_assigned_jobcards',
    'export_missing_buying_prices',
    'export_missing_selling_prices',
    'export_client_payment_details',
    'export_stock_balance',
    'export_monthly_schedule',
    'export_current_selling_prices_and_reorder_levels',
    'export_current_parts_and_partno',
    'export_import_orders',
    'import_selling_prices_and_reorder_levels',
    'get_jobcard_details',
    'get_signature',
    'get_createdAt',
    'fillJobCardReport',
    'createSignedJobcardPdf',
    'get_reports_bootstrap',
]

from . import BMALocal as _compatibility_facade
