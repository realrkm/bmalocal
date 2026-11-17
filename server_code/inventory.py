from ._common import *

# ***************************************************Car Parts Details Section ************************************
@anvil.server.callable()
def getCarPartNames():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Name 
            FROM tbl_carpartnames
            GROUP BY Name 
            ORDER BY Name ASC
        """
        cursor.execute(query)
        result = cursor.fetchall()
        return [{"Name": r[0]} for r in result]


@anvil.server.callable()
def getCarPartNumber(name):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
        SELECT ID, PartNo 
        FROM tbl_carpartnames 
        WHERE Name = %s
        ORDER BY PartNo ASC
        """
        cursor.execute(query, (name,))
        result = cursor.fetchall()
        return [{"ID": r[0], "PartNo": r[1]} for r in result]


@anvil.server.callable()
def getCarPartNameAndNumber(value):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
        SELECT ID, PartNo, Name 
        FROM tbl_carpartnames 
        WHERE PartNo LIKE %s OR Name LIKE %s
        ORDER BY Name ASC
        """
        like_value = f"%{value}%"
        cursor.execute(query, (like_value, like_value))
        result = cursor.fetchall()
        # Return tuples: (Label shown, Value stored)
        return [(f"{r[1]} - {r[2]}", r[0]) for r in result]


@anvil.server.callable()
def getCarPartNamesWithId(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Name 
            FROM tbl_carpartnames
            WHERE ID = %s
        """
        cursor.execute(query, (valueID,))
        result = cursor.fetchall()
        return [{"Name": r[0]} for r in result]


@anvil.server.callable()
def getCarPartIDWithNumber(valueNumber):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID 
            FROM tbl_carpartnames
            WHERE PartNo = %s
        """
        cursor.execute(query, (valueNumber,))
        result = cursor.fetchall()
        # Check if a result was returned
        if result:
            return result[0]  # Return the first (and only) column from the row
        else:
            return None  # Return None if no part was found


@anvil.server.callable()
def getCarPartNumberWithID(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
        SELECT ID, PartNo 
        FROM tbl_carpartnames 
        WHERE ID = %s
        ORDER BY PartNo ASC
        """
        cursor.execute(query, (valueID,))
        result = cursor.fetchall()
        return [{"ID": r[0], "PartNo": r[1]} for r in result]


@anvil.server.callable()
def getSellingPrice(id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Amount 
            FROM tbl_partssellingprice
            WHERE CarPartsNamesID = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        return result

@anvil.server.callable()
def insertMissingSellingPrice(part_id, amount):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_partssellingprice 
                (CarPartsNamesID, Amount, SaleDiscount, SetPriceDate)
            VALUES 
                (%s, %s, 0, CURDATE())
        """
        cursor.execute(query, (part_id, amount))

# *************************************************** Inventory Details Section ************************************


@anvil.server.callable()
def get_filtered_parts(part_filter=""):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
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
            INNER JOIN tbl_partssellingprice psp 
                ON cpn.ID = psp.CarPartsNamesID
            INNER JOIN tbl_stockparts sp 
                ON cpn.ID = sp.CarPart
            INNER JOIN latest_stock ls 
                ON ls.CarPart = cpn.ID AND ls.rn = 1
            LEFT JOIN issued i 
                ON cpn.ID = i.CarPartID
            LEFT JOIN latest_stocktake lst 
                ON cpn.ID = lst.CarPartNameID
            WHERE cpn.Name LIKE %s OR cpn.PartNo LIKE %s
            GROUP BY 
                cpn.Name,
                cpn.PartNo,
                cpn.OrderLevel,
                psp.Amount,
                psp.SaleDiscount,
                cpn.ID,
                ls.UnitCost,
                i.TotalIssued,
                lst.HarmornizedValue
            ORDER BY cpn.Name;
        """

        like_filter = f"%{part_filter}%"
        cursor.execute(query, (like_filter, like_filter))
        rows = cursor.fetchall()

        result = []
        for count, row in enumerate(rows, start=1):
            result.append(
                {
                    "No": count,
                    "Name": row[0],
                    "PartNo": row[1],
                    "ReorderLevel": row[2],
                    "Cost": f"{float(row[3]):,.2f}" if row[3] is not None else None,
                    "Selling": f"{float(row[4]):,.2f}" if row[4] is not None else None,
                    "Discount": row[5],
                    "MaxOfDate": row[6],
                    "StockBalance": f"{float(row[7] or 0):.2f}",
                }
            )

        return result

@anvil.server.callable()
def search_car_parts_location(search_term=""):
    _get_current_user()
    with db_cursor() as cursor:
        # If no search term is provided, avoid unnecessary LIKE scans
        if search_term:
            query = """
                SELECT 
                    n.ID,
                    n.Name,
                    n.PartNo,
                    l.Location
                FROM tbl_carpartnames n
                INNER JOIN tbl_carpartslocation l ON l.ID = n.Location
                WHERE n.Name LIKE %s
                   OR n.PartNo LIKE %s
                   OR l.Location LIKE %s
                ORDER BY n.Name
            """
            like_pattern = f"%{search_term}%"
            params = (like_pattern, like_pattern, like_pattern)
        else:
            query = """
                SELECT 
                    n.ID,
                    n.Name,
                    n.PartNo,
                    l.Location
                FROM tbl_carpartnames n
                INNER JOIN tbl_carpartslocation l ON l.ID = n.Location
                ORDER BY n.Name
            """
            params = ()

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            {"No": count, "Name": row[1], "PartNo": row[2], "Location": row[3]}
            for count, row in enumerate(rows, start=1)
        ]


@anvil.server.callable()
def missing_buying_prices(search_term=""):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT
                tbl_carpartssupplier.Name, 
                tbl_carpartnames.Name, 
                tbl_carpartnames.PartNo, 
                tbl_stockparts.UnitCost
            FROM 
                tbl_carpartnames 
            INNER JOIN 
                tbl_stockparts 
            ON 
                tbl_carpartnames.ID = tbl_stockparts.CarPart
            INNER JOIN 
                tbl_carpartssupplier 
            ON 
                tbl_stockparts.CarPartsSupplierID = tbl_carpartssupplier.ID
            WHERE 
                tbl_stockparts.UnitCost <1
                AND 
                    (tbl_carpartnames.Name LIKE %s 
                        OR 
                     tbl_carpartnames.PartNo LIKE %s )
            ORDER BY 
                tbl_carpartnames.Name
        """

        like_pattern = f"%{search_term}%"

        cursor.execute(query, (like_pattern, like_pattern))
        rows = cursor.fetchall()

        result = []
        for count, row in enumerate(rows, start=1):
            result.append(
                {
                    "No": count,
                    "Supplier": row[0],
                    "Name": row[1],
                    "PartNo": row[2],
                    "Cost": f"{row[3]:,.2f}",
                }
            )

        return result


@anvil.server.callable()
def get_buying_prices(search_term=""):
    _get_current_user()
    with db_cursor() as cursor:
        base_query = """
            SELECT
                sp.Date,
                s.Name AS Supplier,
                cp.Name AS PartName,
                cp.PartNo,
                sp.UnitCost,
                sp.NoOfUnits
            FROM tbl_stockparts sp
            INNER JOIN tbl_carpartnames cp ON cp.ID = sp.CarPart
            INNER JOIN tbl_carpartssupplier s ON s.ID = sp.CarPartsSupplierID
            WHERE sp.UnitCost > 0
        """

        params = []

        # Add search filter only if search_term is provided
        if search_term and search_term.strip():
            base_query += " AND (cp.Name LIKE %s OR cp.PartNo LIKE %s)"
            like_pattern = f"%{search_term.strip()}%"
            params.extend([like_pattern, like_pattern])

        # Always order results
        base_query += " ORDER BY sp.Date DESC, cp.Name"

        cursor.execute(base_query, tuple(params))
        rows = cursor.fetchall()

        result = [
            {
                "No": idx,
                "Date": row[0],
                "Supplier": row[1],
                "Name": row[2],
                "PartNo": row[3],
                "Cost": f"{row[4]:,.2f}",
                "NoOfUnits": row[5],
            }
            for idx, row in enumerate(rows, start=1)
        ]

        return result


@anvil.server.callable()
def get_buying_prices_by_partID(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT
                tbl_stockparts.Date,
                tbl_carpartssupplier.Name, 
                tbl_carpartnames.Name, 
                tbl_carpartnames.PartNo, 
                tbl_stockparts.UnitCost
            FROM 
                tbl_carpartnames 
            INNER JOIN 
                tbl_stockparts 
            ON 
                tbl_carpartnames.ID = tbl_stockparts.CarPart
            INNER JOIN 
                tbl_carpartssupplier 
            ON 
                tbl_stockparts.CarPartsSupplierID = tbl_carpartssupplier.ID
            WHERE 
                tbl_stockparts.UnitCost >0
                AND 
                    tbl_carpartnames.ID = %s
            ORDER BY 
                tbl_stockparts.Date DESC, tbl_carpartnames.Name 
        """

        cursor.execute(query, (valueID,))
        rows = cursor.fetchall()

        result = []
        for count, row in enumerate(rows, start=1):
            result.append(
                {
                    "No": count,
                    "Date": row[0],
                    "Supplier": row[1],
                    "Name": row[2],
                    "PartNo": row[3],
                    "Cost": f"{row[4]:,.2f}",
                }
            )

        return result


@anvil.server.callable()
def missing_selling_prices(search_term=""):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT
                      tbl_carpartssupplier.Name,  
                      tbl_carpartnames.Name, 
                      tbl_carpartnames.PartNo, 
                      tbl_partssellingprice.Amount,
                      tbl_partssellingprice.SaleDiscount
                    FROM 
                      tbl_carpartnames
                    INNER JOIN tbl_stockparts 
                      ON tbl_carpartnames.ID = tbl_stockparts.CarPart
                    INNER JOIN 
                        tbl_carpartssupplier 
                    ON 
                        tbl_stockparts.CarPartsSupplierID = tbl_carpartssupplier.ID
                    LEFT JOIN tbl_partssellingprice 
                      ON tbl_stockparts.CarPart = tbl_partssellingprice.CarPartsNamesID
                    WHERE 
                      tbl_partssellingprice.Amount < 1
                    AND
                                            (tbl_carpartnames.Name LIKE %s 
                                             OR tbl_carpartnames.PartNo LIKE %s )
                    GROUP BY 
                      tbl_carpartnames.Name, 
                      tbl_carpartnames.PartNo, 
                      tbl_partssellingprice.Amount,
                      tbl_carpartssupplier.Name,
                      tbl_partssellingprice.SaleDiscount
                    ORDER BY 
                      tbl_carpartnames.Name   
        """

        like_pattern = f"%{search_term}%"

        cursor.execute(query, (like_pattern, like_pattern))
        rows = cursor.fetchall()

        result = []
        for count, row in enumerate(rows, start=1):
            result.append(
                {
                    "No": count,
                    "Supplier": row[0],
                    "Name": row[1],
                    "PartNo": row[2],
                    "Amount": f"{row[3]:,.2f}",
                    "Discount": None if row[4] is None else f"{float(row[4]):,.2f}",
                }
            )

        return result


@anvil.server.callable()
def get_selling_prices(search_term=""):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT
                      tbl_carpartssupplier.Name,  
                      tbl_carpartnames.Name, 
                      tbl_carpartnames.PartNo, 
                      tbl_partssellingprice.Amount,
                      tbl_partssellingprice.SaleDiscount
                    FROM 
                      tbl_carpartnames
                    INNER JOIN tbl_stockparts 
                      ON tbl_carpartnames.ID = tbl_stockparts.CarPart
                    INNER JOIN 
                        tbl_carpartssupplier 
                    ON 
                        tbl_stockparts.CarPartsSupplierID = tbl_carpartssupplier.ID
                    LEFT JOIN tbl_partssellingprice 
                      ON tbl_stockparts.CarPart = tbl_partssellingprice.CarPartsNamesID
                    WHERE 
                      tbl_partssellingprice.Amount > 0
                    AND
                                            (tbl_carpartnames.Name LIKE %s 
                                             OR tbl_carpartnames.PartNo LIKE %s )
                    GROUP BY 
                      tbl_carpartnames.Name, 
                      tbl_carpartnames.PartNo, 
                      tbl_partssellingprice.Amount,
                      tbl_carpartssupplier.Name,
                      tbl_partssellingprice.SaleDiscount
                    ORDER BY 
                      tbl_carpartnames.Name   
        """

        like_pattern = f"%{search_term}%"

        cursor.execute(query, (like_pattern, like_pattern))
        rows = cursor.fetchall()

        result = []
        for count, row in enumerate(rows, start=1):
            result.append(
                {
                    "No": count,
                    "Supplier": row[0],
                    "Name": row[1],
                    "PartNo": row[2],
                    "Amount": f"{row[3]:,.2f}",
                    "Discount": None if row[4] is None else f"{float(row[4]):,.2f}",
                }
            )

        return result


@anvil.server.callable()
def updatePrice(priceType, newPrice, discount, partNo):
    _get_current_user()
    with db_cursor() as cursor:
        if priceType == "Selling":
            query = """
                UPDATE tbl_partssellingprice
                SET 
                    SetPriceDate = NOW(),
                    Amount = %s,
                    SaleDiscount = %s 
                WHERE CarPartsNamesID = (
                    SELECT ID FROM tbl_carpartnames WHERE PartNo = %s
                )
            """
            cursor.execute(query, (newPrice, discount, partNo))

        elif priceType == "Buying":
            query = """
                UPDATE tbl_stockparts
                SET 
                    Date = NOW(),
                    UnitCost = %s 
                WHERE CarPart = (
                    SELECT ID FROM tbl_carpartnames WHERE PartNo = %s
                )
            """
            cursor.execute(query, (newPrice, partNo))


# *************************************************** Repair Priorities Details Section ************************************


@anvil.server.callable()
def getCarRegNo(search_text=""):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT DISTINCT RegNo
            FROM tbl_jobcarddetails
            WHERE RegNo LIKE %s
            ORDER BY RegNo ASC
        """
        like_pattern = f"%{search_text}%"
        cursor.execute(query, (like_pattern,))
        results = [row[0] for row in cursor.fetchall()]
        return results


@anvil.server.callable()
def getPriorityList(regNo=""):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT RegNo, PartName, PartNumber, Quantity, Amount, Priority
            FROM tbl_repairpriorities
            WHERE RegNo = %s
        """
        cursor.execute(query, (regNo,))
        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "Name": row[1],
                    "Number": row[2],
                    "Quantity": row[3],
                    "Amount": f"{float(row[4]):,.2f}",
                    "Priority": row[5],
                }
            )

        return results


@anvil.server.callable()
def deleteCurrentPriority(regNo):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            DELETE FROM tbl_repairpriorities WHERE RegNo = %s
        """
        cursor.execute(query, (regNo,))


@anvil.server.callable()
def savePriority(assignedDate, regNo, name, number, quantity, amount, priority):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO 
                tbl_repairpriorities(Date,RegNo,PartName,PartNumber,Quantity,Amount,Priority) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query, (assignedDate, regNo, name, number, quantity, amount, priority)
        )


@anvil.server.callable()
def get_priority_list(regNo):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Date, RegNo, PartName, PartNumber, Quantity, Amount, Priority
            FROM tbl_repairpriorities
            WHERE RegNo = %s 
            ORDER BY Priority DESC
        """
        cursor.execute(query, (regNo,))
        rows = cursor.fetchall()

        urgent = []
        can_wait = []

        for count, r in enumerate(rows, start=1):

            def safe_float_convert(value):
                if value is None:
                    return None
                if isinstance(value, (int, float, decimal.Decimal)):
                    return float(value)
                if isinstance(value, str):
                    try:
                        return float(value.replace(",", ""))
                    except ValueError:
                        print(f"Warning: Could not convert string '{value}' to float.")
                        return None
                return None

            quantity_issued_val = safe_float_convert(r[4])
            amount_val = safe_float_convert(r[5])
            display_quantity_issued = (
                ""
                if r[4] is None or not isinstance(r[4], (int, float, decimal.Decimal))
                else quantity_issued_val
            )

            total_calc = None
            if quantity_issued_val is None:
                total_calc = amount_val
            elif amount_val is not None:
                total_calc = round(quantity_issued_val * amount_val, 2)

            entry = {
                "No": count,
                "Date": r[0],
                "RegNo": r[1],
                "PartName": r[2],
                "PartNumber": r[3],
                "Quantity": display_quantity_issued,
                "Amount": amount_val,
                "Total": total_calc,
                "Priority": r[6],
            }

            if str(r[6]).strip().lower() == "urgent":
                urgent.append(entry)
            elif str(r[6]).strip().lower() == "can wait":
                can_wait.append(entry)

        return {"Urgent": urgent, "CanWait": can_wait}


@anvil.server.callable()
def fillFormData(regNo, docType, logo_path: str = os.getenv("LOGO"), font_path: str = os.getenv("FONT_PATH")) -> str:
    _get_current_user()
    if docType == "Priority":
        docTitle = "Repair Priority List"
        priorityDetails = get_priority_list(regNo)
        # Get Date and RegNo
        if priorityDetails["Urgent"]:
            currentDate = priorityDetails["Urgent"][0]["Date"]
        else:
            currentDate = priorityDetails["CanWait"][0]["Date"]

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
    urgent_header = "Urgent"
    items_html_urgent = ""
    # Calculate sub total
    sub_total_urgent = sum(float(item["Total"]) for item in priorityDetails["Urgent"])
    canwait_header = "Can Wait"
    items_html_canwait = ""
    # Calculate sub total
    sub_total_canwait = sum(float(item["Total"]) for item in priorityDetails["CanWait"])

    for item in priorityDetails["Urgent"]:
        items_html_urgent += f"""
                    <tr class="item-row">
                        <td>{item['No']}</td>
                        <td>{item['PartName']}</td>
                        <td>{item['Quantity']}</td>
                        <td>{f"{item['Amount']:,.2f}"}</td>
                        <td>{f"{item['Total']:,.2f}"}</td>
                    </tr>"""

    for item in priorityDetails["CanWait"]:
        items_html_canwait += f"""
                    <tr class="item-row">
                        <td>{item['No']}</td>
                        <td>{item['PartName']}</td>
                        <td>{item['Quantity']}</td>
                        <td>{item['Amount']}</td>
                        <td>{item['Total']}</td>
                    </tr>"""

    if docType in ("Priority"):
        reportNotes = """
                    <div class="notes-section">
                        <div class="notes-title">NOTE: THE ABOVE ESTIMATE IS SUBJECT TO REVIEW DUE TO:</div>
                        <ol class="notes-list">
                            <li>Price change at the time of actual repair</li>
                            <li>Further damages found during repairs</li>
                            <li>100% Deposit on imported parts</li>
                            <li>70% deposit on local parts on commencement</li>
                        </ol>
                    </div>
            """
    else:
        reportNotes = ""

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
                        <span class="detail-label">Date:</span>
                        <div>
                        <span class="detail-value">{currentDate}</span>
                        </div>
                    </div>
                </td>

                <!-- Right Column -->
                <td style="width: 50%; vertical-align: top; padding-left: 32px;">
                    <div class="detail-row">
                        <span class="detail-label">Reg No:</span>
                        <div>
                        <span class="detail-value">{regNo}</span>
                        </div>
                    </div>
                    
                </td>
            </tr>
        </table>
        <!-- END UPDATED -->
        
        <h3 style="text-align: center;"> {urgent_header}</h3>
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
                {items_html_urgent}
                <tr class="total-row">
                    <td colspan="4" style="text-align: right; font-weight: 500;">Total</td>
                    <td style="font-weight: 500;">{sub_total_urgent:,.2f}</td>
                </tr>
            </tbody>
        </table>
        
        <h3 style="text-align: center;"> {canwait_header}</h3>
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
                {items_html_canwait}
                <tr class="total-row">
                    <td colspan="4" style="text-align: right; font-weight: 500;">Total</td>
                    <td style="font-weight: 500;">{sub_total_canwait:,.2f}</td>
                </tr>
            </tbody>
        </table>
    {reportNotes}   
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
def fillDefectsListFormData(
    jobCardID, docType, logo_path: str = os.getenv("LOGO"),font_path: str = os.getenv("FONT_PATH")
) -> str:
    _get_current_user()
    if docType == "DefectsList":
        docTitle = "Defects List"
        defectsdetails = get_defects_list_details_by_job_id(jobCardID)
    elif docType == "PricedDefectsList":
        docTitle = "Priced Defects List"
        defectsdetails = get_priced_defects_list_details_by_job_id(jobCardID)

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

    # === Generate defects rows — escape DB content to prevent XSS ===
    items_html = ""
    for item in defectsdetails["Defects"]:
        items_html += f"""
            <tr class="item-row">
                <td>{html_module.escape(str(item["No"]))}</td>
                <td>{html_module.escape(str(item["Defect"]))}</td>
            </tr>"""

    # === Signature ===
    signature_html = f"""
    <img src="data:image/png;base64,{defectsdetails["Signature"]}" 
         alt="Technician Signature" 
         style="max-width: 90%; height: auto; display: block; border: 1px solid #ccc; padding: 4px;"/>
    """

    # === Full HTML ===
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
                    font-family: 'Roboto', 'Noto', Arial, sans-serif;
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

                .notes-title, .notes-list li, #footer div {{
                    font-family: 'Mozilla Headline', Arial, sans-serif;
                }}

                #footer div {{
                    width: 80%;
                    margin: 0 auto;
                    text-align: center;
                    font-size: 12px;
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

                <div class="header">{docTitle.upper()}</div>

                <table style="width: 100%; table-layout: fixed; margin: 24px 0;">
                    <tr>
                        <td style="width: 50%; vertical-align: top; padding-left: 24px; padding-right: 32px;">
                            <div class="detail-row"><span class="detail-label">Customer Name:</span><div><span class="detail-value">{defectsdetails['ClientName']}</span></div></div>
                            <div class="detail-row"><span class="detail-label">Make And Model:</span><div><span class="detail-value">{defectsdetails['MakeAndModel']}</span></div></div>
                            <div class="detail-row"><span class="detail-label">Reg No:</span><div><span class="detail-value">{defectsdetails['RegNo']}</span></div></div>
                        </td>
                        <td style="width: 50%; vertical-align: top; padding-left: 32px;">
                            <div class="detail-row"><span class="detail-label">Engine:</span><div><span class="detail-value">{defectsdetails['EngineCode']}</span></div></div>
                            <div class="detail-row"><span class="detail-label">Chassis:</span><div><span class="detail-value">{defectsdetails['ChassisNo']}</span></div></div>
                            <div class="detail-row"><span class="detail-label">Date:</span><div><span class="detail-value">{defectsdetails['ReceivedDate']}</span></div></div>
                        </td>
                    </tr>
                </table>

                <table class="items-table">
                    <thead><tr><th>No.</th><th>Defects</th></tr></thead>
                    <tbody>{items_html}</tbody>
                </table>

                <table style="width: 100%; table-layout: fixed; margin: 24px 0;">
                    <tr>
                        <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                            <div class="detail-row"><span class="detail-label">Prepared By:</span><div><span class="detail-value">{defectsdetails['Staff']}</span></div></div>
                        </td>
                        <td style="width: 33.33%; vertical-align: top; padding: 0 16px;">
                            <div class="detail-row">
                                <span class="detail-label">Signature:</span>
                                <div style="width: 100%; overflow: hidden;">
                                    <span class="detail-value" style="display: block; width: 100%;">
                                        {signature_html}
                                    </span>
                                </div>
                            </div>
                        </td>
                    </tr>
                </table>

                <footer id="footer">
                    <div><p>Joy Is The Feeling Of Being Looked After By The Best - BMW CENTER For Your BMW.</p></div>
                </footer>
            </div>
        </body>
        </html>
    """

    return html_content


@anvil.server.callable()
def downloadDefectsPdfForm(jobcardID, docType):
    _get_current_user()
    try:
        result = getJobCardRow(jobcardID)
        docName = result["JobCardRef"]

        if docType == "DefectsList":
            fileName = str(docName) + " Defects List"
        elif docType == "PricedDefectsList":
            fileName = str(docName) + " Priced Defects List"

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

        if docType == "DefectsList" or docType == "PricedDefectsList":
            html_string = fillDefectsListFormData(jobcardID, docType)

        pdfkit.from_string(
            html_string,
            fileName,
            options={**setting_options, "debug-javascript": ""},
            configuration=config,
        )

        media_object = anvil.media.from_file(fileName, "application/pdf", name=fileName)
        return media_object

    except Exception as e:
        print("PDF generation failed:", str(e))
        raise


@anvil.server.callable()
def downloadRevisionPdfForm(regNo, docType):
    _get_current_user()
    try:
        docName = regNo
        if docType == "Priority":
            fileName = str(docName) + " Priority"
        elif docType == "Brand":
            fileName = str(docName) + " Brand"

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

        if docType == "Priority":
            html_string = fillFormData(regNo, docType)
        elif docType == "Brand":
            html_string = fillBrandComparisonFormData(regNo, docType)

        pdfkit.from_string(
            html_string, fileName, options=setting_options, configuration=config
        )
        media_object = anvil.media.from_file(fileName, "application/pdf", name=fileName)
        return media_object

    except Exception as e:
        print("PDF generation failed:", str(e))
        raise


@anvil.server.callable()
def deleteRevisionFile(regNo, docType):
    # Construct file name based on docType
    _get_current_user()
    if docType == "Priority":
        file_name = f"{regNo} Priority"
    elif docType == "Brand":
        file_name = f"{regNo} Brand"
    else:
        return f"Unsupported document type: {docType}"

    # Optional: define file path
    # file_path = os.path.join("/your/path", file_name)
    file_path = file_name  # if no custom directory

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"File '{file_name}' deleted successfully."
        else:
            return f"File '{file_name}' does not exist."
    except Exception as e:
        return f"Error deleting file: {e}"


# *************************************************** Brand Comparison Details Section ************************************


@anvil.server.callable()
def getBrandComparisonList(regNo=""):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT RegNo, PartName, PartNumber, Quantity, Amount, GroupID
            FROM tbl_brandcomparison
            WHERE RegNo = %s
        """
        cursor.execute(query, (regNo,))
        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "Name": row[1],
                    "Number": row[2],
                    "Quantity": row[3],
                    "Amount": (
                        "TO BE CONFIRMED"
                        if float(row[4]) == 0
                        else f"{float(row[4]):,.2f}"
                    ),
                    "GroupID": row[5],
                }
            )

        return results


@anvil.server.callable()
def get_brand_list(regNo):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Date, RegNo, PartName, PartNumber, Quantity, Amount, GroupID
            FROM tbl_brandcomparison
            WHERE RegNo = %s 
            ORDER BY GroupID ASC
        """
        cursor.execute(query, (regNo,))
        rows = cursor.fetchall()

        entry = []
        for count, r in enumerate(rows, start=1):

            def safe_float_convert(value):
                if value is None:
                    return None
                if isinstance(value, (int, float, decimal.Decimal)):
                    return float(value)
                if isinstance(value, str):
                    try:
                        return float(value.replace(",", ""))
                    except ValueError:
                        print(f"Warning: Could not convert string '{value}' to float.")
                        return None
                return None

            quantity_issued_val = safe_float_convert(r[4])
            amount_val = safe_float_convert(r[5])
            display_quantity_issued = (
                ""
                if r[4] is None or not isinstance(r[4], (int, float, decimal.Decimal))
                else quantity_issued_val
            )

            total_calc = None
            if quantity_issued_val is None:
                total_calc = amount_val
            elif amount_val is not None:
                total_calc = round(quantity_issued_val * amount_val, 2)

            entry.append(
                {
                    "No": count,
                    "Date": r[0],
                    "RegNo": r[1],
                    "PartName": r[2],
                    "PartNumber": r[3],
                    "Quantity": display_quantity_issued,
                    "Amount": amount_val,
                    "Total": total_calc,
                    "GroupID": r[6],
                }
            )

        return entry


@anvil.server.callable()
def fillBrandComparisonFormData(
    regNo, docType, logo_path: str = os.getenv("LOGO"),font_path: str = os.getenv("FONT_PATH")
) -> str:
    _get_current_user()
    if docType == "Brand":
        docTitle = "Brand Comparison List"
        comparisonDetails = get_brand_list(regNo)

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

    currentDate = comparisonDetails[0]["Date"]

    # Calculate sub total
    # sub_total = sum(float(item['Total']) for item in comparisonDetails)

    # Group items by GroupID
    grouped_data = defaultdict(list)
    for item in comparisonDetails:
        grouped_data[item["GroupID"]].append(item)

    items_html = ""
    grand_total = 0

    for group_id, group_items in grouped_data.items():
        group_total = sum(item["Total"] or 0 for item in group_items)
        grand_total += group_total

        for item in group_items:
            if item["Amount"] == 0:  # Implies To Be Confirmed
                textAmount = "TO BE CONFIRMED"
            else:
                textAmount = f"{item['Amount']:,.2f}"
            if item["Total"] == 0:  # Implies To Be Confirmed
                textTotal = "TO BE CONFIRMED"
            else:
                textTotal = f"{item['Total']:,.2f}"

            items_html += f"""
                <tr class="item-row">
                    <td>{html_module.escape(str(item['No']))}</td>
                    <td>{html_module.escape(str(item['PartName']))}</td>
                    <td>{html_module.escape(str(item['Quantity']))}</td>
                    <td>{textAmount}</td>
                    <td>{textTotal}</td>
                </tr>
            """

        items_html += f"""
            <tr class="total-row">
                <td colspan="4" style="text-align: right;">Sub Total</td>
                <td>{group_total:,.2f}</td>
            </tr>
            
        """

    # Replace sub_total with grand_total
    sub_total = grand_total

    if docType in ("Brand"):
        reportNotes = """
                    <div class="notes-section">
                        <div class="notes-title">NOTE: THE ABOVE ESTIMATE IS SUBJECT TO REVIEW DUE TO:</div>
                        <ol class="notes-list">
                            <li>Price change at the time of actual repair</li>
                            <li>Further damages found during repairs</li>
                            <li>100% Deposit on imported parts</li>
                            <li>70% deposit on local parts on commencement</li>
                        </ol>
                    </div>
            """
    else:
        reportNotes = ""

        # Complete HTML template with fixed structure
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
                                <span class="detail-label">Date:</span>
                                <div>
                                <span class="detail-value">{currentDate}</span>
                                </div>
                            </div>
                        </td>

                        <!-- Right Column -->
                        <td style="width: 50%; vertical-align: top; padding-left: 32px;">
                            <div class="detail-row">
                                <span class="detail-label">Reg No:</span>
                                <div>
                                <span class="detail-value">{regNo}</span>
                                </div>
                            </div>

                        </td>
                    </tr>
                </table>
                <!-- END UPDATED -->

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
                    </tbody>
                </table>

            {reportNotes} 
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
def deleteCurrentBrandComparison(regNo):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            DELETE FROM tbl_brandcomparison WHERE RegNo = %s
        """
        cursor.execute(query, (regNo,))


@anvil.server.callable()
def saveBrand(assignedDate, regNo, name, number, quantity, amount, groupid):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO 
                tbl_brandcomparison(Date,RegNo,PartName,PartNumber,Quantity,Amount,GroupID) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query, (assignedDate, regNo, name, number, quantity, amount, groupid)
        )


# *************************************************** Location Details Section ************************************


@anvil.server.callable()
def getLocation():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, Location
            FROM tbl_carpartslocation
            ORDER BY Location ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # Return as a list of dicts for Anvil Dropdown
        # label = what user sees, value = what is stored
        dropdown_items = [(row[1], row[0]) for row in results]

    return dropdown_items


@anvil.server.callable()
def addLocation(locationName):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_carpartslocation (Location) VALUES (%s)
        """
        cursor.execute(query, (locationName,))


@anvil.server.callable()
def getLocationName(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, Location 
            FROM tbl_carpartslocation 
            WHERE ID = %s
        """
        cursor.execute(query, (valueID,))
        result = cursor.fetchone()
        if result:
            return result[1]
        return None


@anvil.server.callable()
def updateLocation(value, id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_carpartslocation
            SET Location = %s
            WHERE ID = %s
        """
        cursor.execute(query, (value, id))


# *************************************************** Supplier Details Section ************************************


@anvil.server.callable()
def getSupplier():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, Name
            FROM tbl_carpartssupplier
            Order By Name ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # Return as a list of dicts for Anvil Dropdown
        # label = what user sees, value = what is stored
        dropdown_items = [(row[1], row[0]) for row in results]

    return dropdown_items


@anvil.server.callable()
def addSupplier(supplierName, supplierPhone):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_carpartssupplier (Name, Phone) VALUES (%s, %s)
        """
        cursor.execute(query, (supplierName, supplierPhone))


@anvil.server.callable()
def getSupplierDetails(supplierID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Name, Phone 
            FROM tbl_carpartssupplier 
            WHERE ID = %s
        """
        cursor.execute(query, (supplierID,))
        result = cursor.fetchone()  # Get one row
        if result:
            return {"Name": result[0], "Phone": result[1]}
        else:
            return None


@anvil.server.callable()
def updateSupplier(supplierName, supplierPhone, supplierID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_carpartssupplier
            SET Name = %s, Phone = %s
            WHERE ID = %s
        """
        cursor.execute(query, (supplierName, supplierPhone, supplierID))

# **************************************************** Combined Location and Supplier Details **************************
@anvil.server.callable()
def getLocationAndSupplier():
    _get_current_user()
    with db_cursor() as cursor:
        cursor.execute("SELECT ID, Location FROM tbl_carpartslocation ORDER BY Location ASC")
        locations = [(row[1], row[0]) for row in cursor.fetchall()]

        cursor.execute("SELECT ID, Name FROM tbl_carpartssupplier ORDER BY Name ASC")
        suppliers = [(row[1], row[0]) for row in cursor.fetchall()]

    return {"locations": locations, "suppliers": suppliers}

# *************************************************** New Car Parts Details Section ************************************


@anvil.server.callable()
def addNewParts(
    purchaseDate,
    partName,
    partNumber,
    locationID,
    supplierID,
    units,
    buyingPrice,
    sellingPrice,
    discountPrice,
    reorderLevel,
):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO 
            tbl_carpartnames(Name,PartNo,OrderLevel,Location) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (partName, partNumber, reorderLevel, locationID))

        partID = cursor.lastrowid

        query2 = """
            INSERT INTO 
            tbl_partssellingprice(SetPriceDate, CarPartsNamesID, Amount, SaleDiscount) 
            VALUES (%s,%s,%s,%s)
        """
        cursor.execute(query2, (purchaseDate, partID, sellingPrice, discountPrice))

        query3 = """
          INSERT INTO 
          tbl_stockparts(Date, CarPart, CarPartsSupplierId, NoOfUnits, UnitCost, Narration) 
          VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query3, (purchaseDate, partID, supplierID, units, buyingPrice, " ")
        )


@anvil.server.callable()
def check_duplicate_number(number):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT ID FROM tbl_carpartnames 
                WHERE PartNo = %s
            """
        cursor.execute(query, (number,))

        result = cursor.fetchone()
        return result is not None


@anvil.server.callable()
def getPartsDetailsID(id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                tbl_stockparts.Date,
                tbl_stockparts.NoOfUnits,
                tbl_stockparts.UnitCost,
                tbl_stockparts.CarPartsSupplierID,
                tbl_carpartnames.Name,
                tbl_carpartnames.PartNo,
                tbl_carpartnames.OrderLevel,
                tbl_carpartnames.Location
            FROM tbl_carpartnames
            INNER JOIN tbl_stockparts
                ON tbl_carpartnames.ID = tbl_stockparts.CarPart
            WHERE tbl_carpartnames.ID = %s
            ORDER BY tbl_stockparts.Date DESC
            LIMIT 1
        """
        cursor.execute(query, (id,))
        row = cursor.fetchone()

    if row:
        columns = [
            "Date",
            "NoOfUnits",
            "UnitCost",
            "CarPartsSupplierID",
            "Name",
            "PartNo",
            "OrderLevel",
            "Location",
        ]
        return dict(zip(columns, row))
    else:
        return None


@anvil.server.callable()
def getPartsSellingDetailsID(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT SetPriceDate, Amount, SaleDiscount FROM tbl_partssellingprice 
            WHERE CarPartsNamesID = %s
        """
        cursor.execute(query, (valueID,))
        row = cursor.fetchone()

    if row:
        columns = ["SetPriceDate", "Amount", "SaleDiscount"]
        return dict(zip(columns, row))
    else:
        return None


@anvil.server.callable()
def updateNewParts(
    purchaseDate,
    partName,
    partNumber,
    locationID,
    supplierID,
    units,
    buyingPrice,
    sellingPrice,
    discountPrice,
    reorderLevel,
    valueID,
    oldSupplierID,
):
    _get_current_user()
    with db_cursor() as cursor:

        query = """
                    UPDATE tbl_carpartnames
                    SET 
                        Name = %s,
                        PartNo = %s,
                        OrderLevel = %s,
                        Location = %s 
                    WHERE ID = %s
                """
        cursor.execute(query, (partName, partNumber, reorderLevel, locationID, valueID))

        query2 = """
            INSERT INTO tbl_partssellingprice
                (SetPriceDate, CarPartsNamesID, Amount, SaleDiscount)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                SetPriceDate = VALUES(SetPriceDate),
                Amount = VALUES(Amount),
                SaleDiscount = VALUES(SaleDiscount)
        """
        cursor.execute(query2, (purchaseDate, valueID, sellingPrice, discountPrice))

        query3 = """
                  UPDATE tbl_stockparts
                  SET 
                    Date = %s, 
                    CarPart = %s,
                    CarPartsSupplierID = %s, 
                    NoOfUnits = %s, 
                    UnitCost = %s
                 WHERE CarPart = %s and CarPartsSupplierID = %s
                """
        cursor.execute(
            query3,
            (
                purchaseDate,
                valueID,
                supplierID,
                units,
                buyingPrice,
                valueID,
                oldSupplierID,
            ),
        )


@anvil.server.callable()
def addStock(additionDate, supplierID, partID, no_of_units, unit_cost):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO 
                tbl_stockparts(Date, CarPart, CarPartsSupplierID, NoOfUnits, UnitCost, Narration) 
            VALUES  
                (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query, (additionDate, partID, supplierID, no_of_units, unit_cost, "")
        )

# ***************************************************  Car Parts Where Buying Price Exceeds Selling Price Section ************************************
@anvil.server.callable()
def getPartsWhereBuyingPriceExceedsSelling(logged_in_user):
    _get_current_user()
    
    if not logged_in_user:
        return []

    with db_cursor() as cursor:
        query = """
            WITH latest_stock AS (
                SELECT sp.CarPart, sp.UnitCost
                FROM tbl_stockparts sp
                INNER JOIN (
                    SELECT CarPart, MAX(ID) AS max_id
                    FROM tbl_stockparts
                    GROUP BY CarPart
                ) latest
                ON sp.CarPart = latest.CarPart 
                AND sp.ID = latest.max_id
            )
            SELECT 
                cpn.Name,
                cpn.PartNo,
                ls.UnitCost AS Cost,
                psp.Amount AS Selling,
                psp.SaleDiscount AS Discount
            FROM tbl_carpartnames cpn
            INNER JOIN tbl_partssellingprice psp 
                ON cpn.ID = psp.CarPartsNamesID
                AND psp.Amount > -1
            INNER JOIN latest_stock ls 
                ON cpn.ID = ls.CarPart
            WHERE 
                ls.UnitCost IS NOT NULL
                AND psp.Amount IS NOT NULL
                AND ls.UnitCost > psp.Amount
            ORDER BY cpn.Name
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        result = []
        for count, row in enumerate(rows, start=1):
            result.append({
                "No": count,
                "Name": row[0],
                "PartNo": row[1],
                "Cost": f"{float(row[2] or 0):,.2f}" if row[2] is not None else None,
                "Selling": f"{float(row[3] or 0):,.2f}" if row[3] is not None else None,
                "Discount": row[4],
                "BuyingPriceExceedsSelling": "Yes"
            })

        return result
    
# *************************************************** Stock Balance Details Section ************************************


@anvil.server.callable()
def get_car_parts_summary(search_term=""):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
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
            FROM (
                SELECT ID, Name, PartNo, OrderLevel
                FROM tbl_carpartnames
                WHERE Name LIKE %s OR PartNo LIKE %s
            ) cp
            LEFT JOIN tbl_stockparts sp ON cp.ID = sp.CarPart
            LEFT JOIN issued i ON cp.ID = i.CarPartID
            LEFT JOIN latest_stocktake l ON cp.ID = l.CarPartNameID
            GROUP BY 
                cp.ID,
                cp.Name,
                cp.PartNo,
                cp.OrderLevel,
                i.TotalIssued,
                l.HarmornizedValue
            ORDER BY cp.Name
        """

        like_pattern = f"%{search_term}%"
        cursor.execute(query, (like_pattern, like_pattern))
        rows = cursor.fetchall()

        result = []
        for idx, row in enumerate(rows, start=1):
            row_data = {
                "No": idx,
                "Name": row[1],
                "PartNo": row[2],
                "OrderLevel": row[3],
                "TotalIssued": float(row[4] or 0),
                "LatestStockTake": float(row[5] or 0),
                "TotalStock": float(row[7] or 0),
                "StockBalance": f"{float(row[8] or 0):.2f}",
                "BelowOrderLevel": row[9],
            }
            result.append(row_data)
       
        return result


# ***************************************************Car Parts Used Section ************************************


@anvil.server.callable()
def get_car_parts_used(job_card_id):
    _get_current_user()
    with db_cursor() as cursor:
        if job_card_id is None:
            query = """
                SELECT 
                    tbl_assignedcarparts.Date, tbl_jobcarddetails.JobCardRef, tbl_carpartnames.Name, tbl_carpartnames.PartNo, 
                    tbl_assignedcarparts.QuantityIssued, tbl_jobcarddetails.MakeAndModel
                FROM 
                    tbl_jobcarddetails 
                INNER JOIN 
                    (tbl_carpartnames 
                INNER JOIN 
                    tbl_assignedcarparts ON tbl_carpartnames.ID = tbl_assignedcarparts.CarPartID) 
                ON 
                    tbl_jobcarddetails.ID = tbl_assignedcarparts.AssignedJobID
                ORDER BY 
                    tbl_assignedcarparts.Date DESC
                """
            cursor.execute(query)

        else:
            query2 = """
                SELECT 
                    tbl_assignedcarparts.Date, tbl_jobcarddetails.JobCardRef, tbl_carpartnames.Name, tbl_carpartnames.PartNo, 
                    tbl_assignedcarparts.QuantityIssued, tbl_jobcarddetails.MakeAndModel
                FROM 
                    tbl_jobcarddetails 
                INNER JOIN 
                    (tbl_carpartnames 
                INNER JOIN 
                    tbl_assignedcarparts ON tbl_carpartnames.ID = tbl_assignedcarparts.CarPartID) 
                ON 
                    tbl_jobcarddetails.ID = tbl_assignedcarparts.AssignedJobID
                WHERE 
                    tbl_jobcarddetails.ID = %s
                ORDER BY 
                    tbl_assignedcarparts.Date DESC

            """
            cursor.execute(query2, (job_card_id,))

        rows = cursor.fetchall()
        result = []
        for idx, row in enumerate(rows, start=1):
            row_data = {
                "No": idx,
                "AssignedDate": row[0],
                "JobCardRef": row[1],
                "PartName": row[2],
                "PartNo": row[3],
                "Quantity": row[4],
                "MakeAndModel": row[5],
            }
            result.append(row_data)
        return result


@anvil.server.callable()
def get_job_card_from_car_parts_used(search_term):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT
                tbl_assignedcarparts.Date,
                tbl_jobcarddetails.JobCardRef,
                tbl_carpartnames.Name,
                tbl_carpartnames.PartNo,
                tbl_assignedcarparts.QuantityIssued,
                tbl_jobcarddetails.MakeAndModel
            FROM
                tbl_jobcarddetails
            INNER JOIN(
                    tbl_carpartnames
                INNER JOIN tbl_assignedcarparts ON tbl_carpartnames.ID = tbl_assignedcarparts.CarPartID
                )
            ON
                tbl_jobcarddetails.ID = tbl_assignedcarparts.AssignedJobID
            WHERE
                tbl_carpartnames.PartNo LIKE %s
            ORDER BY
                tbl_assignedcarparts.Date
            DESC
        """
        cursor.execute(query, (f"%{search_term}%",))
        rows = cursor.fetchall()

        result = []
        for idx, row in enumerate(rows, start=1):
            result.append(
                {
                    "No": idx,
                    "AssignedDate": row[0],
                    "JobCardRef": row[1],
                    "PartName": row[2],
                    "PartNo": row[3],
                    "Quantity": row[4],
                    "MakeAndModel": row[5],
                }
            )
        return result


# ***************************************************Assigned JobCard Details Section ************************************


@anvil.server.callable()
def get_assigned_jobs(startDate, endDate, technicianID):
    _get_current_user()
    with db_cursor() as cursor:
        if startDate is None and endDate is None and technicianID is None:
            query = """
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
                    FROM 
                        tbl_invoices AS i
                    INNER JOIN 
                        tbl_jobcarddetails AS jd ON i.AssignedJobID = jd.ID
                    INNER JOIN 
                        tbl_pendingassignedjobs AS pj ON jd.ID = pj.JobCardRefID
                    INNER JOIN 
                        tbl_technicians AS t ON t.ID = pj.TechnicianID
                    GROUP BY 
                        jd.ReceivedDate, 
                        jd.JobCardRef, 
                        t.Fullname,
                        jd.MakeAndModel
                    ORDER BY 
                        jd.ReceivedDate DESC

            """
            cursor.execute(query)

        elif startDate is not None and endDate is not None and technicianID is None:
            query2 = """
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
                    FROM 
                        tbl_invoices AS i
                    INNER JOIN 
                        tbl_jobcarddetails AS jd ON i.AssignedJobID = jd.ID
                    INNER JOIN 
                        tbl_pendingassignedjobs AS pj ON jd.ID = pj.JobCardRefID
                    INNER JOIN 
                        tbl_technicians AS t ON t.ID = pj.TechnicianID
                    WHERE 
                        jd.ReceivedDate BETWEEN %s AND %s 
                    GROUP BY 
                        jd.ReceivedDate, 
                        jd.JobCardRef, 
                        t.Fullname,
                        jd.MakeAndModel
                    ORDER BY 
                        jd.ReceivedDate DESC

            """
            cursor.execute(query2, (startDate, endDate))

        elif startDate is None and endDate is None and technicianID is not None:
            query3 = """
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
                    FROM 
                        tbl_invoices AS i
                    INNER JOIN 
                        tbl_jobcarddetails AS jd ON i.AssignedJobID = jd.ID
                    INNER JOIN 
                        tbl_pendingassignedjobs AS pj ON jd.ID = pj.JobCardRefID
                    INNER JOIN 
                        tbl_technicians AS t ON t.ID = pj.TechnicianID
                    WHERE 
                        pj.TechnicianID = %s
                    GROUP BY 
                        jd.ReceivedDate, 
                        jd.JobCardRef, 
                        t.Fullname,
                        jd.MakeAndModel
                    ORDER BY 
                        jd.ReceivedDate DESC

            """
            cursor.execute(query3, (technicianID,))

        elif startDate is not None and endDate is not None and technicianID is not None:
            query4 = """
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
                    FROM 
                        tbl_invoices AS i
                    INNER JOIN 
                        tbl_jobcarddetails AS jd ON i.AssignedJobID = jd.ID
                    INNER JOIN 
                        tbl_pendingassignedjobs AS pj ON jd.ID = pj.JobCardRefID
                    INNER JOIN 
                        tbl_technicians AS t ON t.ID = pj.TechnicianID
                    WHERE 
                        (jd.ReceivedDate BETWEEN %s AND %s) AND pj.TechnicianID = %s 
                    GROUP BY 
                        jd.ReceivedDate, 
                        jd.JobCardRef, 
                        t.Fullname,
                        jd.MakeAndModel
                    ORDER BY 
                        jd.ReceivedDate DESC

            """
            cursor.execute(query4, (startDate, endDate, technicianID))

        rows = cursor.fetchall()
        result = []
        for idx, row in enumerate(rows, start=1):
            result.append(
                {
                    "No": idx,
                    "ReceivedDate": row[0],
                    "JobCardRef": row[1],
                    "Technician": row[2],
                    "InvoicedAmount": f"{row[3]:,.2f}",
                    "LabourAmount": f"{row[4]:,.2f}",
                    "MakeAndModel": row[5],
                }
            )
        return result



# *************************************************** Resolve Part Number from Barcode Section ************************************
@anvil.server.callable()
def resolve_part(barcode_or_partno):
    _get_current_user()
    with db_cursor() as cursor:
        # 1. Check in tbl_carpartnames.PartNo
        cursor.execute(
            "SELECT PartNo, Name FROM tbl_carpartnames WHERE PartNo = %s",
            (barcode_or_partno,),
        )
        row = cursor.fetchone()
        if row:
            return {"PartNo": row[0], "Name": row[1]}

        # 2. Check in tbl_barcodepartnomapping.Barcode
        cursor.execute(
            "SELECT PartNo FROM tbl_barcodepartnomapping WHERE Barcode = %s",
            (barcode_or_partno,),
        )
        row = cursor.fetchone()
        if row:
            partno = row[0]
            # lookup in carpartnames
            cursor.execute(
                "SELECT PartNo, Name FROM tbl_carpartnames WHERE PartNo = %s", (partno,)
            )
            carpart = cursor.fetchone()
            if carpart:
                return {"PartNo": carpart[0], "Name": carpart[1]}

        # Not found
        return None


@anvil.server.callable()
def saveBarcodePartNo(barcode, partno):
    _get_current_user()

    try:
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tbl_barcodepartnomapping (Barcode, PartNo)
                VALUES (%s, %s)
                """,
                (barcode, partno),
            )

        return {
            "success": True,
            "message": f"Barcode '{barcode}' is mapped to PartNo '{partno}'."
        }

    except mysql.connector.IntegrityError as e:
        # Duplicate key error (1062)
        if e.errno == 1062:
            return {
                "success": False,
                "message": f"This barcode '{barcode}' is already mapped to PartNo '{partno}'."
            }

        # Any other integrity error
        return {
            "success": False,
            "message": "Database integrity error occurred."
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

# *************************************************** Stocktake Harmonization Section ************************************

def _process_stocktake_item(cursor, part_no, quantity):
    quantity=float(quantity)

    """
    Core stocktake logic, reusable by both save_stocktake and import_counting_stock_quantity.
    Expects an already-open cursor.
    Returns True if processed, False if part not found.
    """
    # 1. Get CarPartName info
    cursor.execute("""
        SELECT cp.ID, cp.Name, cp.PartNo, cp.OrderLevel, cl.Location
        FROM tbl_carpartnames cp
        LEFT JOIN tbl_carpartslocation cl ON cp.Location = cl.ID
        WHERE cp.PartNo = %s
    """, (part_no,))
    result = cursor.fetchone()
    if not result:
        return False
    carpart_id, carpart_name, part_number, reorder_level, location = result

    # 2. Get TotalStock and TotalIssued
    cursor.execute("""
        SELECT 
            COALESCE(SUM(sp.NoOfUnits), 0),
            COALESCE(i.TotalIssued, 0)
        FROM tbl_carpartnames cp
        LEFT JOIN tbl_stockparts sp ON cp.ID = sp.CarPart
        LEFT JOIN (
            SELECT CarPartID, SUM(QuantityIssued) AS TotalIssued
            FROM tbl_assignedcarparts
            GROUP BY CarPartID
        ) i ON cp.ID = i.CarPartID
        WHERE cp.ID = %s
        GROUP BY cp.ID
    """, (carpart_id,))
    stock_info = cursor.fetchone()
    total_stock, total_issued = stock_info if stock_info else (0, 0)

    # 3. Balance and Variance
    total_stock=float(total_stock or 0.0)
    total_issued = float(total_issued or 0.0)

    balance = total_stock - total_issued
    balance = float(balance or 0.0)
    variance = quantity - balance

    # 4. Comment logic
    if quantity < balance:
        comment = "System Count > Actual Count"
    elif quantity > balance:
        comment = "Actual Stock > System Stock"
    else:
        comment = "Stock Balanced"

    # 5. Insert/Update tbl_stocktakeharmonized
    cursor.execute("""
        INSERT INTO tbl_stocktakeharmonized (StockTakeDate, CarPartNameID, HarmornizedValue)
        VALUES (CURDATE(), %s, %s)
        ON DUPLICATE KEY UPDATE HarmornizedValue = VALUES(HarmornizedValue)
    """, (carpart_id, variance))

    # 6. Insert/Update tbl_finalcapturedstocktaking
    cursor.execute("""
        INSERT INTO tbl_finalcapturedstocktaking
            (CountingDate, CarPart, PartNumber, ReorderLevel, Location, Balance, CapturedQuantity, Variance, Comment)
        VALUES (CURDATE(), %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            CarPart = VALUES(CarPart),
            ReorderLevel = VALUES(ReorderLevel),
            Location = VALUES(Location),
            Balance = VALUES(Balance),
            CapturedQuantity = VALUES(CapturedQuantity),
            Variance = VALUES(Variance),
            Comment = VALUES(Comment)
    """, (carpart_name, part_number, reorder_level, location, balance, quantity, variance, comment))

    return True


@anvil.server.callable()
def save_stocktake(repeating_panel_data):
    """
    repeating_panel_data is expected to be a list of dicts:
    [
        {"PartNo": "ABC123", "Name": "Brake Pad", "Quantity": 20},
        {"PartNo": "XYZ456", "Name": "Oil Filter", "Quantity": 15},
        ...
    ]
    """
    _get_current_user()
    skipped = []

    with db_cursor() as cursor:
        for item in repeating_panel_data:
            try:
                part_no = item["PartNo"]
                quantity = float(item["Quantity"])
            except (KeyError, ValueError, TypeError) as e:
                skipped.append(f"Invalid item {item}: {e}")
                continue

            processed = _process_stocktake_item(cursor, part_no, quantity)
            if not processed:
                skipped.append(f"PartNo '{part_no}' not found in database — skipped.")

    result = "Stocktake saved/updated successfully."
    if skipped:
        result += f"\n{len(skipped)} item(s) skipped:\n" + "\n".join(skipped)
    return result


@anvil.server.callable()
def import_counting_stock_quantity(file):
    _get_current_user()

    # Load the uploaded Excel file from Anvil media object
    file_bytes = BytesIO(file.get_bytes())
    wb = load_workbook(file_bytes, data_only=True)
    ws = wb.active

    # Validate headers
    expected_headers = ["No", "Name", "PartNo", "Quantity"]
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
            if num < 0:
                return False, "negative"
            return True, num
        except (ValueError, TypeError):
            return False, "not a number"

    updated_count = 0
    skipped_rows = []

    with db_cursor() as cursor:
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            no, name, part_no, quantity = row

            # Skip completely empty rows
            if all(v is None for v in row):
                continue

            # Validate required fields
            if not name or not part_no:
                skipped_rows.append(f"Row {row_idx}: Missing Name or PartNo — skipped.")
                continue

            # Validate Quantity
            valid, quantity_result = is_valid_number(quantity)
            if not valid:
                if quantity_result == "negative":
                    skipped_rows.append(f"Row {row_idx} ({name}): Quantity cannot be negative ({quantity}) — skipped.")
                else:
                    skipped_rows.append(f"Row {row_idx} ({name}): Quantity is not a valid number — skipped.")
                continue

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

            # Process stocktake for this row
            processed = _process_stocktake_item(cursor, str(part_no).strip(), float(quantity_result))
            if not processed:
                skipped_rows.append(f"Row {row_idx} ({name} / {part_no}): Stocktake processing failed — skipped.")
                continue

            updated_count += 1

    # Build result summary
    summary = f"{updated_count} part(s) updated successfully."
    if skipped_rows:
        summary += f"\n{len(skipped_rows)} row(s) skipped:\n" + "\n".join(skipped_rows)

    return summary


# *************************************************** Stock Analysis Report Section ************************************


@anvil.server.callable()
def get_stock_analysis_report(start_date=None, end_date=None, partnumber=None):

    _get_current_user()
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    header_date = now.strftime("%A, %d %B %Y")
    header_time = now.strftime("%H:%M:%S")

    # --- Styles & Header ---
    html_parts = [
        f""" 
        <style> 
            body {{ 
                  font-family: "Mozilla Headline", Arial, Helvetica, sans-serif; font-size: 15px; margin: 0; padding: 10px; 
                  }} 
            .header {{ 
                  display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; 
                  }} 
            .report-title {{
                   font-size: 20px; font-weight: bold; 
                  }}
             .datetime {{ 
                  text-align: right; font-size: 14px; color: #333; 
                  }}
            .table-note {{ 
                  border: 2px solid red; 
                  color: red; 
                  font-weight: bold; 
                  padding: 8px; 
                  margin: 10px 0; 
                  text-align: center; 
                  font-size: 16px;
                  border-radius: 6px; 
                  background-color: #ffe6e6; /* light red background for emphasis */
                   }} 
            .table-container {{
                   overflow-x: auto; -webkit-overflow-scrolling: touch; max-height: 70vh; 
                  }}
            table {{ 
                  border-collapse: collapse; width: 100%; min-width: 900px; margin-top: 10px; 
                  }}
            th, td {{
                   padding: 6px 10px; border: 1px solid #999; text-align: left; white-space: normal;
                   }} 
            th {{
                   background-color: #0074D9; color: #fff; position: sticky; top: 0; z-index: 2; 
                  }} 
            .comment-red {{ 
                  background-color: #ff4d4d; color: #fff; font-weight: bold; 
                  }}
            .comment-yellow {{ 
                  background-color: #ffd633; font-weight: bold; 
                  }}
            .comment-green {{ 
                  background-color: #00A300; color: #fff; font-weight: bold; 
                  }}
            </style> 
                  <div class="header"> 
                    <div class="report-title">Stock Analysis Report</div> 
                    <div class="datetime"> {header_date}<br>{header_time} </div> 
                  </div> 
                 <div class="table-note"> 
                    <div>System Stock = Total Stock Bought - Total Stock Issued</div>
                    <div>Variance = Actual Stock - System Stock</div>
                 </div> 
                 <div class="table-container"> 
            <table> 
             <tr> 
               <th>Date</th> 
               <th>Location</th> 
               <th>Name</th> 
               <th>PartNo</th> 
               <th>Reorder Level</th> 
               <th>System Stock</th> 
               <th>Actual Stock</th> 
               <th>Variance</th> 
               <th>Comment</th> 
               </tr> 
        """
    ]

    # --- Query ---
    query = """
        SELECT 
          CountingDate,
          Location,
          CarPart,
          PartNumber,
          ReorderLevel,
          Balance AS SystemStock,
          CapturedQuantity AS ActualStock,
          Variance,
          Comment
        FROM tbl_finalcapturedstocktaking
        WHERE 1=1
    """
    params = []

    if start_date and end_date:
        query += " AND CountingDate BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    if partnumber:
        query += " AND PartNumber = %s"
        params.append(partnumber)

    query += " ORDER BY CountingDate DESC, Location, CarPart"

    with db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        

    # --- Build Rows ---
    current_date = None
    current_location = None
    row_parts = []

    for (
        counting_date,
        location,
        carpart,
        partnumber,
        reorder,
        system_stock,
        actual_stock,
        variance,
        comment,
    ) in rows:

        date_cell = ""
        location_cell = ""

        if counting_date != current_date:
            date_cell = counting_date.strftime("%d/%m/%Y")
            current_date = counting_date
            current_location = None

        if location != current_location:
            location_cell = location
            current_location = location

        if comment and "System Count > Actual Count" in comment:
            comment_class = "comment-red"
        elif comment and "Actual Stock > System Stock" in comment:
            comment_class = "comment-yellow"
        elif comment and "Stock Balanced" in comment:
            comment_class = "comment-green"
        else:
            comment_class = ""

        row_parts.append(
            f"""
        <tr>
          <td>{date_cell}</td>
          <td>{location_cell}</td>
          <td>{carpart}</td>
          <td>{partnumber}</td>
          <td>{reorder}</td>
          <td>{system_stock}</td>
          <td>{actual_stock}</td>
          <td>{variance}</td>
          <td class="{comment_class}">{comment or ''}</td>
        </tr>
        """
        )

    html_parts.append("".join(row_parts))
    html_parts.append("</table></div>")
    return "".join(html_parts)

__all__ = [
    'getCarPartNames',
    'getCarPartNumber',
    'getCarPartNameAndNumber',
    'getCarPartNamesWithId',
    'getCarPartIDWithNumber',
    'getCarPartNumberWithID',
    'getSellingPrice',
    'insertMissingSellingPrice',
    'get_filtered_parts',
    'search_car_parts_location',
    'missing_buying_prices',
    'get_buying_prices',
    'get_buying_prices_by_partID',
    'missing_selling_prices',
    'get_selling_prices',
    'updatePrice',
    'getCarRegNo',
    'getPriorityList',
    'deleteCurrentPriority',
    'savePriority',
    'get_priority_list',
    'fillFormData',
    'fillDefectsListFormData',
    'downloadDefectsPdfForm',
    'downloadRevisionPdfForm',
    'deleteRevisionFile',
    'getBrandComparisonList',
    'get_brand_list',
    'fillBrandComparisonFormData',
    'deleteCurrentBrandComparison',
    'saveBrand',
    'getLocation',
    'addLocation',
    'getLocationName',
    'updateLocation',
    'getSupplier',
    'addSupplier',
    'getSupplierDetails',
    'updateSupplier',
    'getLocationAndSupplier',
    'addNewParts',
    'check_duplicate_number',
    'getPartsDetailsID',
    'getPartsSellingDetailsID',
    'updateNewParts',
    'addStock',
    'getPartsWhereBuyingPriceExceedsSelling',
    'get_car_parts_summary',
    'get_car_parts_used',
    'get_job_card_from_car_parts_used',
    'get_assigned_jobs',
    'resolve_part',
    'saveBarcodePartNo',
    '_process_stocktake_item',
    'save_stocktake',
    'import_counting_stock_quantity',
    'get_stock_analysis_report',
]

from . import BMALocal as _compatibility_facade
