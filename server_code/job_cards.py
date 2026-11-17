from ._common import *

# ***************************************************Job Card Details Section ************************************


@anvil.server.callable()
def getJobCardInstructions(id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT ClientInstruction 
                FROM tbl_jobcarddetails 
                WHERE ID = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        if result:
            raw_instructions = result[0]

            # Step 1: Remove all HTML tags like <div>, <br>, etc.
            text_only = re.sub(r"<[^>]+>", "", raw_instructions)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""


@anvil.server.callable()
def getJobCardTechNotes(id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT Notes 
                FROM tbl_jobcarddetails 
                WHERE ID = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        if result:
            raw_instructions = result[0]

            # Step 1: Remove all HTML tags like <div>, <br>, etc.
            text_only = re.sub(r"<[^>]+>", "", raw_instructions)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""


# Return a specific row from job card table
@anvil.server.callable()
def getJobCardRow(IdValue):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                ID, ClientDetails, RegNo, MakeAndModel, ChassisNo,
                EngineCC, EngineNo, EngineCode, Manual, Auto,
                PaintCode, Comp, TPO, JobCardRef,ReceivedDate, DueDate, ExpDate,
                CheckedInBy, Spare, Jack, Brace, OtherItems, Mileage, `Empty`, `Quarter`, Half,
                ThreeQuarter, `Full`, ClientInstruction, Notes, Status  
            FROM tbl_jobcarddetails 
            WHERE ID = %s 
        """
        cursor.execute(query, (IdValue,))
        result = cursor.fetchone()
        if result:
            x = {
                "ID": result[0],
                "ClientDetails": result[1],
                "RegNo": result[2],
                "MakeAndModel": result[3],
                "ChassisNo": result[4],
                "EngineCC": result[5],
                "EngineNo": result[6],
                "EngineCode": result[7],
                "Manual": result[8],
                "Auto": result[9],
                "PaintCode": result[10],
                "Comprehensive": result[11],
                "ThirdParty": result[12],
                "JobCardRef": result[13],
                "ReceivedDate": result[14],
                "DueDate": result[15],
                "ExpDate": result[16],
                "CheckedInBy": result[17],
                "Spare": result[18],
                "Jack": result[19],
                "Brace": result[20],
                "OtherItems": result[21],
                "Mileage": result[22],
                "Empty": result[23],
                "Quarter": result[24],
                "Half": result[25],
                "ThreeQuarter": result[26],
                "Full": result[27],
                "ClientInstruction": result[28],
                "Notes": result[29],
                "Status": result[30],
            }

            return x
        else:
            return None


@anvil.server.callable()
def getJobCardRowWithClientID(IdValue):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                ID, ClientDetails, RegNo, MakeAndModel, ChassisNo, EngineCode  
            FROM tbl_jobcarddetails 
            WHERE ID = (
                SELECT MAX(ID)
                FROM tbl_jobcarddetails
                WHERE ClientDetails = %s
            )
        """
        cursor.execute(query, (IdValue,))
        result = cursor.fetchone()
        if result:
            return {
                "ID": result[0],
                "ClientDetails": result[1],
                "RegNo": result[2],
                "MakeAndModel": result[3],
                "ChassisNo": result[4],
                "EngineCode": result[5],
            }
        else:
            return None

# Check for job card ref duplicate
@anvil.server.callable()
def check_job_card_duplicate(JobCardRef):
    """Check if a job card reference already exists in the database."""
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT COUNT(*) FROM tbl_jobcarddetails 
            WHERE JobCardRef = %s 
        """
        cursor.execute(query, (JobCardRef,))
        result = cursor.fetchone()
        return result[0] > 0


# Save new job card data
@anvil.server.callable()
def save_job_card_details(
    technicianDetails,
    ClientDetails,
    JobCardRef,
    ReceivedDate,
    DueDate,
    ExpDate,
    CheckedInBy,
    Ins,
    Comp,
    TPO,
    Spare,
    Jack,
    Brace,
    OtherItems,
    RegNo,
    MakeAndModel,
    ChassisNo,
    EngineCC,
    Mileage,
    EngineNo,
    EngineCode,
    Manual,
    Auto,
    Empty,
    Quarter,
    Half,
    ThreeQuarter,
    Full,
    PaintCode,
    ClientInstruction,
    Notes,
    IsComplete,
    Status,
):
    _get_current_user()
    with db_cursor() as cursor:
        # Insert into tbl_jobcarddetails
        query = """
            INSERT INTO tbl_jobcarddetails (
                ClientDetails, JobCardRef, ReceivedDate, DueDate, ExpDate, CheckedInBy,
                Ins, Comp, TPO, Spare, Jack, Brace, OtherItems, RegNo, MakeAndModel, ChassisNo,
                EngineCC, Mileage, EngineNo, EngineCode, Manual, Auto, `Empty`, `Quarter`,
                `Half`, `ThreeQuarter`, `Full`, PaintCode, ClientInstruction, Notes, IsComplete, Status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        values = (
            ClientDetails,
            JobCardRef,
            ReceivedDate,
            DueDate,
            ExpDate,
            CheckedInBy,
            Ins,
            Comp,
            TPO,
            Spare,
            Jack,
            Brace,
            OtherItems,
            RegNo,
            MakeAndModel,
            ChassisNo,
            EngineCC,
            Mileage,
            EngineNo,
            EngineCode,
            Manual,
            Auto,
            Empty,
            Quarter,
            Half,
            ThreeQuarter,
            Full,
            PaintCode,
            ClientInstruction,
            Notes,
            IsComplete,
            Status,
        )
        cursor.execute(query, values)

        # Get the ID of the newly inserted job card
        job_card_id = cursor.lastrowid

        # Insert into tbl_pendingassignedjobs using the returned ID
        query2 = """
            INSERT INTO tbl_pendingassignedjobs (
                JobCardRefID, TechnicianID, DateAssigned
            ) 
            VALUES (%s, %s, NOW())
        """
        values2 = (
            job_card_id,  # The ID of the inserted job card
            technicianDetails,  # The technician
        )
        cursor.execute(query2, values2)


# Get job card id to assign in tbl_pendingassignedjobs
@anvil.server.callable()
def getJobCardID(jobCardRef):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID FROM tbl_jobcarddetails 
            WHERE JobCardRef = %s 
        """
        cursor.execute(query, (jobCardRef,))
        result = cursor.fetchone()
        return result[0] if result else None


@anvil.server.callable()
def getJobCardRef(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, JobCardRef
            FROM tbl_jobcarddetails
            WHERE ID = %s
            ORDER BY RegNo ASC
        """

        cursor.execute(query, (valueID,))
        result = cursor.fetchall()
        return [{"ID": r[0], "JobCardRef": r[1]} for r in result]


@anvil.server.callable()
def getQuotationInvoiceName(jobCardID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT JobCardRef
            FROM tbl_jobcarddetails
            WHERE ID = %s
        """

        cursor.execute(query, (jobCardID,))
        result = cursor.fetchone()
        return result[0]


@anvil.server.callable()
def get_all_jobcards_by_status():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
        SELECT Status, COUNT(*)
        FROM tbl_jobcarddetails 
        WHERE Status IN (
            'Checked In', 'Create Quote', 'Confirm Quote',
            'In Service', 'Verify Task', 'Issue Invoice', 'Ready for Pickup'
        )
        GROUP BY Status
        """
        cursor.execute(query)
        result = cursor.fetchall()

        # Returns lightweight list placeholders so len(all_data.get(status, [])) works seamlessly
        jobcards = {}
        for status, count in result:
            jobcards[status] = [None] * count

        return jobcards



@anvil.server.callable()
def getTechnicianJobCards(status=None, regNo=None):
    _get_current_user()
    with db_cursor() as cursor:
        # If both filters are missing, return empty list
        if status is None and regNo is None:
            return []

        base_query = """
            SELECT 
                tbl_jobcarddetails.ID, 
                tbl_jobcarddetails.MakeAndModel, 
                tbl_jobcarddetails.JobCardRef, 
                tbl_jobcarddetails.RegNo, 
                tbl_jobcarddetails.DueDate, 
                tbl_jobcarddetails.ClientInstruction, 
                tbl_jobcarddetails.Status, 
                tbl_technicians.Fullname, 
                tbl_jobcarddetails.ChassisNo
            FROM 
                tbl_jobcarddetails 
            INNER JOIN 
                tbl_pendingassignedjobs 
            ON 
                tbl_jobcarddetails.ID = tbl_pendingassignedjobs.JobCardRefID
            INNER JOIN 
                tbl_technicians 
            ON 
                tbl_technicians.ID = tbl_pendingassignedjobs.TechnicianID
        """

        conditions = []
        params = []

        # Add filters dynamically
        if status is not None:
            conditions.append("tbl_jobcarddetails.Status = %s")
            params.append(status)

        if regNo is not None:
            conditions.append("tbl_jobcarddetails.RegNo = %s")
            params.append(regNo)

        # Combine WHERE conditions
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        base_query += " ORDER BY tbl_jobcarddetails.DueDate DESC"

        cursor.execute(base_query, tuple(params))
        result = cursor.fetchall()

        # Clean and return
        jobcards = []
        for r in result:
            instruction = r[5] or ""
            text_only = re.sub(r"<[^>]+>", "", instruction)
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]
            clean_instruction = "\n".join(lines)

            card = {
                "id": r[0],
                "make": r[1],
                "jobcardref": r[2],
                "plate": r[3],
                "date": r[4],
                "instruction": clean_instruction,
                "status": r[6],
                "technician": r[7],
                "chassis": r[8],
            }
            jobcards.append(card)

        return jobcards


@anvil.server.callable()
def getJobCardRefEditDetails():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT
                ID,
                JobCardRef
            FROM
                tbl_jobcarddetails
            WHERE
                (Status = 'Checked In' OR Status IS NULL)
                AND IsComplete = 0
            ORDER BY
                JobCardRef DESC;
        """
        cursor.execute(query)
        result = cursor.fetchall()
        return [(r[1], r[0]) for r in result]  # (Display Text, Value)


@anvil.server.callable()
def getJobCardDetailsWithNameSearch(value):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, JobCardRef
                FROM
                    tbl_jobcarddetails
                WHERE
                     JobCardRef Like %s
                ORDER BY
                    Mileage DESC;
        """
        like_value = f"%{value}%"
        cursor.execute(query, (like_value,))
        results = cursor.fetchall()

        # Return in format suitable for dropdown: [(display_text, value), ...]
        return [(row[1], row[0]) for row in results]  # (JobCardRef, ID)


@anvil.server.callable()
def getJobCardDetailsWithRefOrFullnameSearch(value):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                tbl_jobcarddetails.ID, 
                tbl_jobcarddetails.JobCardRef,
                tbl_clientcontacts.Fullname
            FROM
                tbl_jobcarddetails
            JOIN
                tbl_clientcontacts
                ON tbl_jobcarddetails.ClientDetails = tbl_clientcontacts.ID
            WHERE
                LOWER(tbl_jobcarddetails.JobCardRef) LIKE LOWER(%s)
                OR LOWER(tbl_clientcontacts.Fullname) LIKE LOWER(%s)
            ORDER BY
                tbl_jobcarddetails.ReceivedDate DESC;
        """
        like_value = f"%{value}%"
        cursor.execute(query, (like_value, like_value))
        results = cursor.fetchall()

        # Return format: ("Fullname - JobCardRef", ID)
        return [(f"{row[2]} - {row[1]}", row[0]) for row in results]


@anvil.server.callable()
def update_job_card_details(
    jobcardID,
    technicianDetails,
    ClientDetails,
    JobCardRef,
    ReceivedDate,
    DueDate,
    ExpDate,
    CheckedInBy,
    Ins,
    Comp,
    TPO,
    Spare,
    Jack,
    Brace,
    OtherItems,
    RegNo,
    Chassis,
    MakeAndModel,
    EngineCC,
    Mileage,
    EngineNo,
    EngineCode,
    Manual,
    Auto,
    Empty,
    Quarter,
    Half,
    ThreeQuarter,
    Full,
    PaintCode,
    ClientInstruction,
    Notes,
    workDone,
):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_jobcarddetails
            SET
                ClientDetails = %s, JobCardRef = %s, ReceivedDate = %s,DueDate = %s,ExpDate = %s,CheckedInBy = %s,
                TPO = %s,Comp = %s,Spare = %s,Jack = %s, Brace = %s, OtherItems = %s, RegNo = %s, ChassisNo = %s, MakeAndModel = %s,
                EngineCC = %s, Mileage = %s,EngineNo = %s,EngineCode = %s,Manual = %s, Auto = %s, `Empty` = %s,
                `Quarter` = %s,Half = %s, ThreeQuarter = %s, `Full` = %s, PaintCode = %s, ClientInstruction = %s,Notes = %s
            WHERE ID = %s
        """
        values = (
            ClientDetails,
            JobCardRef,
            ReceivedDate,
            DueDate,
            ExpDate,
            CheckedInBy,
            TPO,
            Comp,
            Spare,
            Jack,
            Brace,
            OtherItems,
            RegNo,
            Chassis,
            MakeAndModel,
            EngineCC,
            Mileage,
            EngineNo,
            EngineCode,
            Manual,
            Auto,
            Empty,
            Quarter,
            Half,
            ThreeQuarter,
            Full,
            PaintCode,
            ClientInstruction,
            Notes,
            jobcardID,
        )

        cursor.execute(query, values)

        query2 = """
            UPDATE tbl_pendingassignedjobs 
            SET 
                TechnicianID=%s, DateAssigned=Now()
            WHERE JobCardRefID = %s
        """
        values2 = (technicianDetails, jobcardID)
        cursor.execute(query2, values2)

        # --- Query 3: Check if WorkDone exists, then Update or Insert ---
        
        # 1. Check if the record exists for this JobCardRefID
        cursor.execute(
            "SELECT 1 FROM tbl_workdoneinjobcard WHERE JobCardRefID = %s", 
            (jobcardID,)
        )
        record_exists = cursor.fetchone() is not None

        if record_exists:
            # 2a. If it exists, UPDATE it
            query3 = "UPDATE tbl_workdoneinjobcard SET WorkDone = %s WHERE JobCardRefID = %s"
            cursor.execute(query3, (workDone, jobcardID))
        else:
            # 2b. If it does NOT exist, INSERT it
            query3 = "INSERT INTO tbl_workdoneinjobcard (JobCardRefID, WorkDone) VALUES (%s, %s)"
            cursor.execute(query3, (jobcardID, workDone))


@anvil.server.callable()
def saveSignedJobCardDetails(jobCardId, signature, CreatedAt):
    _get_current_user()
    with db_cursor() as cursor:
        # Read binary content from Anvil media object
        signature_bytes = signature.get_bytes()

        query = """
            INSERT INTO tbl_signedjobcards (AssignedJobID, Signature, CreatedAt)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                Signature = VALUES(Signature),
                CreatedAt = VALUES(CreatedAt)
        """
        cursor.execute(query, (jobCardId, signature_bytes, CreatedAt))


@anvil.server.callable()
def getCheckedInJobcards(jobCardRef):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, JobCardRef
            FROM tbl_jobcarddetails
            WHERE Status = 'Checked In' AND IsComplete = 0 and JobCardRef LIKE %s
            ORDER BY JobCardRef DESC;
        """
        cursor.execute(query, (f"%{jobCardRef}%",))
        result = cursor.fetchall()
        return [(r[1], r[0]) for r in result]


@anvil.server.callable()
def saveCancellationReason(jobcardid, reason):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_cancelledjobcards (AssignedJobID, Reason, CreatedAt)
            VALUES (%s, %s, NOW())
        """
        cursor.execute(query, (jobcardid, reason))


@anvil.server.callable()
def getCancelledJobcardReason(id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT Reason 
                FROM tbl_cancelledjobcards 
                WHERE AssignedJobID = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return ""


@anvil.server.callable()
def getRegNoUsingStatus(status=None, regNo=None):
    _get_current_user()
    with db_cursor() as cursor:
        if status and regNo:
            query = """
                SELECT DISTINCT RegNo
                FROM tbl_jobcarddetails
                WHERE Status = %s AND RegNo LIKE %s
                ORDER BY RegNo ASC
            """
            cursor.execute(query, (status, f"%{regNo}%"))
        elif status:
            query = """
                SELECT DISTINCT RegNo
                FROM tbl_jobcarddetails
                WHERE Status = %s
                ORDER BY RegNo ASC
            """
            cursor.execute(query, (status,))
        elif regNo:
            query = """
                SELECT DISTINCT RegNo
                FROM tbl_jobcarddetails
                WHERE RegNo LIKE %s
                ORDER BY RegNo ASC
            """
            cursor.execute(query, (f"%{regNo}%",))
        else:
            return []

        result = cursor.fetchall()
        return [r[0] for r in result]



@anvil.server.callable()
def getWorkDoneInJobCard(jobcardID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT WorkDone 
            FROM tbl_workdoneinjobcard
            WHERE JobCardRefID = %s
        """
        cursor.execute(query, (jobcardID,))
        result = cursor.fetchone()
        if result:
            raw_workDone = result[0]

            # Step 1: Remove all HTML tags like <div>, <br>, etc.
            text_only = re.sub(r"<[^>]+>", "", raw_workDone)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""

# ***************************************************Progress Tracker Refresh Details Section ************************************

@anvil.server.callable()
def get_progress_tracker_data(job_id):
    _get_current_user()

    with db_cursor() as cursor:

        query = """
            SELECT
                j.ID,
                j.ClientDetails,
                j.RegNo,
                j.MakeAndModel,
                j.Mileage,
                j.ReceivedDate,
                j.Status,

                c.Fullname,
                c.Phone,

                (
                    SELECT i.Status
                    FROM tbl_invoices i
                    WHERE i.AssignedJobID = j.ID
                    ORDER BY i.ID DESC
                    LIMIT 1
                ) AS InvoiceStatus

            FROM tbl_jobcarddetails j

            INNER JOIN tbl_clientcontacts c
                ON c.ID = j.ClientDetails

            WHERE j.ID = %s
            LIMIT 1
        """

        cursor.execute(query, (job_id,))
        row = cursor.fetchone()

        if not row:
            return None

        # Invoice grand total — mirrors get_invoice_total_by_job_id
        cursor.execute(
            """
            SELECT SUM(COALESCE(QuantityIssued, 1) * Amount)
            FROM tbl_invoices
            WHERE AssignedJobID = %s
            """,
            (job_id,),
        )
        total_row = cursor.fetchone()
        invoice_total = (
            f"{float(total_row[0]):,.2f}"
            if total_row and total_row[0] is not None
            else 0.0
        )

        # Previous payments — mirrors get_previous_payment
        cursor.execute(
            """
            SELECT SUM(AmountPaid)
            FROM tbl_payments
            WHERE JobCardRefID = %s
            """,
            (job_id,),
        )
        pay_row = cursor.fetchone()
        previous_payment = (
            f"{float(pay_row[0]):,.2f}"
            if pay_row and pay_row[0] is not None
            else 0.0
        )

        # Cancellation reason — only fetched when status is "Cancel Jobcard"
        cancelled_reason = ""
        if row[6] == "Cancel Jobcard":
            cursor.execute(
                "SELECT Reason FROM tbl_cancelledjobcards WHERE AssignedJobID = %s",
                (job_id,),
            )
            reason_row = cursor.fetchone()
            cancelled_reason = reason_row[0] if reason_row else ""

        return {
            "job_card": {
                "ID": row[0],
                "ClientDetails": row[1],
                "RegNo": row[2],
                "MakeAndModel": row[3],
                "Mileage": row[4],
                "ReceivedDate": row[5],
                "Status": row[6],
            },

            "client": {
                "Fullname": row[7],
                "Phone": row[8],
            },

            "invoice_status": row[9],
            "invoice_total": invoice_total,
            "previous_payment": previous_payment,
            "cancelled_reason": cancelled_reason,
        }

# ********************************************Tech Notes Document Section ************************************
@anvil.server.callable()
def get_tech_notes_details_by_job_id(jobCardID):
    """
    Returns detailed job card information including:
      - Client name
      - Vehicle details
      - Technician name
      - Cleaned and enumerated technician's notes
    """
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                tbl_clientcontacts.Fullname AS ClientName,
                tbl_jobcarddetails.RegNo,
                tbl_jobcarddetails.MakeAndModel,
                tbl_jobcarddetails.EngineCode,
                tbl_jobcarddetails.ChassisNo,
                tbl_jobcarddetails.ReceivedDate,
                tbl_technicians.Fullname AS TechnicianName,
                tbl_jobcarddetails.Notes
            FROM tbl_jobcarddetails
            JOIN tbl_clientcontacts 
                ON tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails
            JOIN tbl_pendingassignedjobs 
                ON tbl_pendingassignedjobs.JobCardRefID = tbl_jobcarddetails.ID
            JOIN tbl_technicians 
                ON tbl_technicians.ID = tbl_pendingassignedjobs.TechnicianID
            WHERE tbl_jobcarddetails.ID = %s;

        """
        cursor.execute(query, (jobCardID,))
        result = cursor.fetchone()

        if not result:
            return None

        # Unpack query result
        (
            client_name,
            reg_no,
            make_model,
            engine_code,
            chassis_no,
            received_date,
            technician_name,
            notes,
        ) = result

        # --- Clean and process notes text ---
        if notes:
            # Step 1: Remove HTML tags (<div>, <br>, etc.)
            text_only = re.sub(r"<[^>]+>", "", notes)

            # Step 2: Split into lines, remove empty ones
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Enumerate notes
            numbered_notes = [
                {"No": i + 1, "Notes": line} for i, line in enumerate(lines)
            ]
        else:
            numbered_notes = []


        # --- Return combined data ---
        return {
            "ClientName": client_name,
            "RegNo": reg_no,
            "MakeAndModel": make_model,
            "EngineCode": engine_code,
            "ChassisNo": chassis_no,
            "ReceivedDate": str(received_date),
            "TechnicianName": technician_name,
            "Notes": numbered_notes,
        }
    
@anvil.server.callable()
def fillTechNotesFormData(jobCardID, docType, logo_path: str = os.getenv("LOGO"),font_path: str = os.getenv("FONT_PATH")) -> str:
    _get_current_user()
    if docType == "TechNotes":
        docTitle = "Technician Notes"
        technotes = get_tech_notes_details_by_job_id(jobCardID)

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
    for item in technotes["Notes"]:
        items_html += f"""
        <tr class="item-row">
            <td>{html_module.escape(str(item["No"]))}</td>
            <td>{html_module.escape(str(item["Notes"]))}</td>
        </tr>"""

    # === Full HTML ===
    html_content = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{html_module.escape(str(docTitle))}</title>
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
                            <div class="detail-row"><span class="detail-label">Customer Name:</span><div><span class="detail-value">{html_module.escape(str(technotes['ClientName']))}</span></div></div>
                            <div class="detail-row"><span class="detail-label">Make And Model:</span><div><span class="detail-value">{html_module.escape(str(technotes['MakeAndModel']))}</span></div></div>
                            <div class="detail-row"><span class="detail-label">Reg No:</span><div><span class="detail-value">{html_module.escape(str(technotes['RegNo']))}</span></div></div>
                        </td>
                        <td style="width: 50%; vertical-align: top; padding-left: 32px;">
                            <div class="detail-row"><span class="detail-label">Engine:</span><div><span class="detail-value">{html_module.escape(str(technotes['EngineCode']))}</span></div></div>
                            <div class="detail-row"><span class="detail-label">Chassis:</span><div><span class="detail-value">{html_module.escape(str(technotes['ChassisNo']))}</span></div></div>
                            <div class="detail-row"><span class="detail-label">Date:</span><div><span class="detail-value">{html_module.escape(str(technotes['ReceivedDate']))}</span></div></div>
                        </td>
                    </tr>
                </table>

                <table class="items-table">
                    <thead><tr><th>No.</th><th>Technician Notes</th></tr></thead>
                    <tbody>{items_html}</tbody>
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
def downloadTechNotesPdfForm(jobcardID, docType):
    _get_current_user()
    try:
        result = getJobCardRow(jobcardID)
        docName = result["JobCardRef"]

        if docType == "TechNotes":
            fileName = str(docName) + " Technician Notes"

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

        html_string = fillTechNotesFormData(jobcardID, docType)

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
def getTechNotes(jobcardID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Notes
            FROM tbl_jobcarddetails
            WHERE ID = %s
        """
        cursor.execute(query, (jobcardID,))
        result = cursor.fetchone()
        text_only = re.sub(r"<[^>]+>", "", result[0])
        return text_only if result else ""  

# ***************************************************Technician Details Section ************************************

@anvil.server.callable()
def saveTecnicianDefectsAndRequestedParts(
    jobcardref, defects, priceddefects, requiredparts, staffID, signature
):
    _get_current_user()
    with db_cursor() as cursor:
        # Read binary content from Anvil media object
        signature_bytes = signature.get_bytes()

        query = """
            INSERT INTO tbl_techniciandefectsandrequestedparts (JobCardRefID, Defects, PricedDefectsList, RequestedParts,PreparedByStaff,Signature)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query, (jobcardref, defects, priceddefects, requiredparts, staffID, signature_bytes)
        )

        
@anvil.server.callable()
def getJobCardDefects(id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT Defects 
                FROM tbl_techniciandefectsandrequestedparts 
                WHERE JobCardRefID = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()

        if result:
            raw_instructions = result[0]

            # Step 1: Remove all HTML tags like <div>, <br>, etc.
            text_only = re.sub(r"<[^>]+>", "", raw_instructions)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""

@anvil.server.callable()
def getJobCardPricedDefects(id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT PricedDefectsList 
                FROM tbl_techniciandefectsandrequestedparts 
                WHERE JobCardRefID = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()

        if result:
            raw_instructions = result[0]

            # Step 1: Remove all HTML tags like <div>, <br>, etc.
            text_only = re.sub(r"<[^>]+>", "", raw_instructions)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""


@anvil.server.callable()
def deleteDefects(JobCardID):
    _get_current_user()
    with db_cursor() as cursor:
        # Delete existing records in tbl_techniciandefectsandrequestedparts
        query_delete = """
            DELETE FROM tbl_techniciandefectsandrequestedparts
            WHERE JobCardRefID = %s
        """
        cursor.execute(query_delete, (JobCardID,))

@anvil.server.callable()
def getRequestedParts(id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT RequestedParts 
                FROM tbl_techniciandefectsandrequestedparts 
                WHERE JobCardRefID = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        if result:
            raw_instructions = result[0]

            # Step 1: Remove all HTML tags like <div>, <br>, etc.
            text_only = re.sub(r"<[^>]+>", "", raw_instructions)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""


@anvil.server.callable()
def getDefectsStaffAndSignature(jobcardref_id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT PreparedByStaff, Signature 
            FROM tbl_techniciandefectsandrequestedparts
            WHERE JobCardRefID = %s
            ORDER BY ID DESC
        """
        cursor.execute(query, (jobcardref_id,))
        results = cursor.fetchall()

        # Convert signatures to BlobMedia for Anvil use
        formatted_results = []
        for row in results:
            prepared_by_id = row[0]
            signature_bytes = row[1]

            signature_media = None
            if signature_bytes:
                signature_media = anvil.BlobMedia("image/png", signature_bytes)

                formatted_results.append(
                    {"PreparedByStaff": prepared_by_id, "Signature": signature_media}
                )

        return formatted_results


@anvil.server.callable()
def updateJobCardStatus(jobcardid, status):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                        UPDATE tbl_jobcarddetails 
                        SET Status = %s 
                        WHERE ID = %s;
                    """
        cursor.execute(query, (status, jobcardid))


@anvil.server.callable()
def saveWorkDoneInJobCard(jobcardID, workDone):
    _get_current_user()
    with db_cursor() as cursor:
        
        # 1. Check if the record exists for this JobCardRefID
        cursor.execute("SELECT 1 FROM tbl_workdoneinjobcard WHERE JobCardRefID = %s", (jobcardID,))
        record_exists = cursor.fetchone() is not None
        
        if record_exists:
            # 2a. If it exists, UPDATE it
            query1 = "UPDATE tbl_workdoneinjobcard SET WorkDone = %s WHERE JobCardRefID = %s"
            cursor.execute(query1, (workDone, jobcardID))
        else:
            # 2b. If it does NOT exist, INSERT it
            query2 = "INSERT INTO tbl_workdoneinjobcard (JobCardRefID, WorkDone) VALUES (%s, %s)"
            cursor.execute(query2, (jobcardID, workDone))

        #New technician portal notification
        publish_technician_portal_notification(jobcardID, "Jobcard transitioned to Verify Task from Technician Portal")
            


@anvil.server.callable()
def updateDefectsList(
    jobcardID, instructions, notes, defects, priceddefects, parts, staffId, signature
):
    _get_current_user()
    with db_cursor() as cursor:
        
        query1 = """
            UPDATE tbl_jobcarddetails
            SET ClientInstruction = %s, Notes = %s
            WHERE ID = %s
        """
        cursor.execute(query1, (instructions, notes, jobcardID))

        if signature:
            # Read binary content from Anvil media object
            signature_bytes = signature.get_bytes()

            query2 = """
                UPDATE tbl_techniciandefectsandrequestedparts
                SET Defects = %s, PricedDefectsList=%s, RequestedParts = %s, PreparedByStaff = %s, Signature = %s
                WHERE JobCardRefID = %s
            """
            cursor.execute(
                query2, (defects, priceddefects, parts, staffId, signature_bytes, jobcardID)
            )

        else:
            query3 = """
                UPDATE tbl_techniciandefectsandrequestedparts
                SET Defects = %s, PricedDefectsList=%s, RequestedParts = %s, PreparedByStaff = %s
                WHERE JobCardRefID = %s
            """
            cursor.execute(query3, (defects, priceddefects, parts, staffId, jobcardID))

@anvil.server.callable()
def transitionCheckedInToCreateQuote():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                UPDATE 
                    tbl_jobcarddetails AS jobs
                INNER JOIN 
                    tbl_techniciandefectsandrequestedparts AS defects 
                ON 
                    jobs.ID = defects.JobCardRefID
                SET 
                    jobs.Status = 'Create Quote'
                WHERE 
                    jobs.Status = 'Checked In';
            """
        cursor.execute(query)

@anvil.server.callable()
def updateBlankDefectsAndRequestedParts():
    _get_current_user()
    with db_cursor() as cursor:
        query1 = """
                UPDATE tbl_techniciandefectsandrequestedparts SET Defects="None" WHERE Defects ="";
            """
        cursor.execute(query1)
        query2 = """
                UPDATE tbl_techniciandefectsandrequestedparts SET PricedDefectsList="None" WHERE PricedDefectsList ="";
            """
        cursor.execute(query2)
        query3 = """
                UPDATE tbl_techniciandefectsandrequestedparts SET RequestedParts="None" WHERE RequestedParts ="";
            """
        cursor.execute(query3)


@anvil.server.callable()
def getDefectsList(jobcardID):
    """
    Joins job card details with technician defects and returns 
    data including a base64 encoded signature.
    """
    _get_current_user()
    query = """
        SELECT
            j.ClientInstruction, 
            j.Notes, 
            t.Defects,
            t.PricedDefectsList,
            t.TechnicianPortalRequestedParts,
            t.RequestedParts, 
            t.PreparedByStaff, 
            t.Signature
        FROM tbl_jobcarddetails j
        JOIN tbl_techniciandefectsandrequestedparts t ON t.JobCardRefID = j.ID
        WHERE j.ID = %s
        ORDER BY t.ID DESC
    """
    
    with db_cursor() as cursor:
        cursor.execute(query, (jobcardID,))
        results = cursor.fetchall()

    formatted_data = []
    
    for row in results:
        instruction, notes, defects, pricedDefects, portalParts, parts, staff, sig_bytes = row
        
        signature_media = None
        if sig_bytes:
            signature_media = anvil.BlobMedia("image/png", sig_bytes)

        formatted_data.append({
            "Instruction": instruction,
            "Notes": notes,
            "Defects": defects,
            "PricedDefects": pricedDefects,
            "TechnicianPortalRequestedParts": portalParts if portalParts else "None",
            "RequestedParts": parts,
            "PreparedByStaff": staff,
            "Signature": signature_media  # This is now an anvil.BlobMedia object
        })

    return formatted_data


@anvil.server.callable()
def get_defects_form_init_data(job_id):
    """
    Combined bootstrap endpoint for DefectsForm:
    Returns defects data, fallback job card instructions/notes, and staff/technician names
    in a single round-trip and DB connection.
    """
    _get_current_user()
    with db_cursor() as cursor:
        # 1. Fetch technician defects list (mirrors getDefectsList)
        query_defects = """
            SELECT
                j.ClientInstruction, 
                j.Notes, 
                t.Defects,
                t.PricedDefectsList,
                t.TechnicianPortalRequestedParts,
                t.RequestedParts, 
                t.PreparedByStaff, 
                t.Signature
            FROM tbl_jobcarddetails j
            JOIN tbl_techniciandefectsandrequestedparts t ON t.JobCardRefID = j.ID
            WHERE j.ID = %s
            ORDER BY t.ID DESC
        """
        cursor.execute(query_defects, (job_id,))
        results = cursor.fetchall()

        formatted_defects = []
        for row in results:
            instruction, notes, defects, pricedDefects, portalParts, parts, staff, sig_bytes = row
            signature_media = anvil.BlobMedia("image/png", sig_bytes) if sig_bytes else None
            formatted_defects.append({
                "Instruction": instruction,
                "Notes": notes,
                "Defects": defects,
                "PricedDefects": pricedDefects,
                "TechnicianPortalRequestedParts": portalParts if portalParts else "None",
                "RequestedParts": parts,
                "PreparedByStaff": staff,
                "Signature": signature_media,
            })

        # 2. Fallback job card details (only if defects list is empty or instruction is empty)
        fallback = None
        has_instruction = bool(formatted_defects and formatted_defects[0].get("Instruction"))
        if not has_instruction:
            cursor.execute(
                "SELECT ClientInstruction, Notes FROM tbl_jobcarddetails WHERE ID = %s",
                (job_id,)
            )
            jc_row = cursor.fetchone()
            if jc_row:
                fallback = {
                    "ClientInstruction": jc_row[0] or "",
                    "Notes": jc_row[1] or "",
                }

        # 3. Fetch staff and technician names (mirrors getStaffAndTechnicianNames)
        query_staff = """
            SELECT Staff AS combined_name FROM tbl_checkstaff WHERE IsArchived = FALSE
            UNION ALL
            SELECT Fullname AS combined_name FROM tbl_technicians WHERE IsArchived = FALSE
            ORDER BY combined_name ASC
        """
        cursor.execute(query_staff)
        staff_results = cursor.fetchall()
        staff_names = []
        for r in staff_results:
            val = r['combined_name'] if isinstance(r, dict) else r[0]
            staff_names.append((val, val))

        return {
            "defects_list": formatted_defects,
            "fallback": fallback,
            "staff_names": staff_names,
        }


# ***************************************************Verify Task  Details Section ************************************


@anvil.server.callable()
def saveConfirmationDetails(jobCardId, remarks, signature, dateCompleted, verify_checklist=None):
    _get_current_user()
    if type(jobCardId) is not int or jobCardId <= 0:
        raise ValueError("Invalid job card ID.")
    if verify_checklist is not None and not isinstance(verify_checklist, dict):
        raise ValueError("Invalid Final Quality and Handover checklist.")

    checklist_values = {}
    if verify_checklist:
        checkbox_names = (
            "chk_final",
            "chk_torque",
            "chk_road_test",
            "chk_engine_clean",
            "chk_old_parts",
            "chk_invoice_explain",
        )
        checkbox_aliases = {
            "chk_test": "chk_road_test",
            "chk_clean": "chk_engine_clean",
            "chk_old": "chk_old_parts",
            "chk_explain": "chk_invoice_explain",
        }
        field_names = (
            "next_service_date",
            "next_service_mileage",
            "time_start",
            "time_end",
            "efficiency",
        )
        allowed_names = set(checkbox_names + field_names + tuple(checkbox_aliases))
        if set(verify_checklist) - allowed_names:
            raise ValueError("Invalid Final Quality and Handover checklist.")

        checklist_values = dict(verify_checklist)
        for legacy_name, current_name in checkbox_aliases.items():
            if current_name not in checklist_values and legacy_name in checklist_values:
                checklist_values[current_name] = checklist_values[legacy_name]
        if "chk_final" not in checklist_values:
            checklist_values["chk_final"] = all(
                checklist_values.get(name) is True
                for name in (
                    "chk_torque",
                    "chk_road_test",
                    "chk_engine_clean",
                    "chk_old_parts",
                    "chk_invoice_explain",
                )
            )
        for name in checkbox_names:
            checklist_values.setdefault(name, False)
            if type(checklist_values[name]) is not bool:
                raise ValueError("Invalid Final Quality and Handover checkbox.")
        for name in field_names:
            checklist_values.setdefault(name, None)
            value = checklist_values.get(name)
            if value is not None and (
                not isinstance(value, str) or len(value) > 1000
            ):
                raise ValueError("Invalid Final Quality and Handover field.")
        if not all(
            checklist_values[name] is True for name in checkbox_names
        ):
            raise ValueError(
                "All Final Quality and Handover checkboxes must be completed."
            )

    with db_cursor() as cursor:
        # Read binary content from Anvil media object
        signature_bytes = signature.get_bytes() if signature else None

        # 1. Insert or update completed jobcard confirmation
        cursor.execute(
            "SELECT ID FROM tbl_completedjobcards WHERE AssignedJobCardID = %s",
            (jobCardId,),
        )
        existing_completed = cursor.fetchone()

        if existing_completed:
            cursor.execute(
                """
                UPDATE tbl_completedjobcards
                SET Remarks = %s, Signature = %s, DateCompleted = %s
                WHERE AssignedJobCardID = %s
                """,
                (remarks, signature_bytes, dateCompleted, jobCardId),
            )
        else:
            cursor.execute(
                """
                INSERT INTO tbl_completedjobcards (AssignedJobCardID, Remarks, Signature, DateCompleted)
                VALUES (%s, %s, %s, %s)
                """,
                (jobCardId, remarks, signature_bytes, dateCompleted),
            )

        # 2. Update job card to completed
        query2 = """
            UPDATE tbl_jobcarddetails SET tbl_jobcarddetails.IsComplete = 1
            WHERE ID = %s
        """
        cursor.execute(query2, (jobCardId,))

        # 3. Save or update Final Quality & Handover JSON in tbl_technicianinspectionchecklist
        if verify_checklist:
            all_checked = all(
                checklist_values[name] is True
                for name in (
                    "chk_final",
                    "chk_torque",
                    "chk_road_test",
                    "chk_engine_clean",
                    "chk_old_parts",
                    "chk_invoice_explain",
                )
            )
            field_components = {
                "next_service_date": "date_picker_next_service",
                "next_service_mileage": "txt_next_service_mileage",
                "time_start": "date_picker_time_start",
                "time_end": "date_picker_time_end",
                "efficiency": "txt_efficiency",
            }
            fields_json = [
                {
                    "name": name,
                    "label": _VEHICLE_INSPECTION_PDF_FIELD_LABELS.get(
                        name, name.replace("_", " ").title()
                    ),
                    "value": checklist_values[name],
                }
                for name in (
                    "chk_final",
                    "chk_torque",
                    "chk_road_test",
                    "chk_engine_clean",
                    "chk_old_parts",
                    "chk_invoice_explain",
                )
            ]
            fields_json.extend(
                {
                    "name": component_name,
                    "label": _VEHICLE_INSPECTION_PDF_FIELD_LABELS[component_name],
                    "value": checklist_values[name],
                }
                for name, component_name in field_components.items()
            )
            cursor.execute(
                """
                INSERT INTO tbl_technicianinspectionchecklist
                    (JobCardRefID, ItemCode, SectionCode, SectionTitle, ItemDescription, IsChecked, FieldsJSON)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    SectionTitle = VALUES(SectionTitle),
                    ItemDescription = VALUES(ItemDescription),
                    IsChecked = VALUES(IsChecked),
                    FieldsJSON = VALUES(FieldsJSON),
                    UpdatedAt = CURRENT_TIMESTAMP
                """,
                (
                    jobCardId,
                    "F1",
                    "F",
                    "F. FINAL QUALITY AND HANDOVER",
                    "Final Quality And Handover Checklist",
                    1 if all_checked else 0,
                    json.dumps(fields_json),
                ),
            )


@anvil.server.callable()
def getVerifyTaskChecklist(jobCardId):
    """Fetch saved Final Quality & Handover JSON for a job card if it exists."""
    _get_current_user()
    if type(jobCardId) is not int or jobCardId <= 0:
        raise ValueError("Invalid job card ID.")
    with db_cursor() as cursor:
        try:
            cursor.execute(
                """
                SELECT
                    (
                        SELECT FieldsJSON
                        FROM tbl_technicianinspectionchecklist
                        WHERE JobCardRefID = %s AND ItemCode = 'F1'
                        LIMIT 1
                    ),
                    (
                        SELECT MAX(UpdatedAt)
                        FROM tbl_technicianinspectionchecklist
                        WHERE JobCardRefID = %s
                    )
                """,
                (jobCardId, jobCardId),
            )
            row = cursor.fetchone()
            if not row or (row[0] is None and row[1] is None):
                return None

            raw = row[0]
            data = (
                json.loads(raw)
                if isinstance(raw, (str, bytes))
                else raw
                if raw is not None
                else {}
            )
            if isinstance(data, list):
                verify_fields = {}
                field_aliases = {
                    "date_picker_next_service": "next_service_date",
                    "txt_next_service_mileage": "next_service_mileage",
                    "date_picker_time_start": "time_start",
                    "date_picker_time_end": "time_end",
                    "txt_efficiency": "efficiency",
                }
                for field in data:
                    if not isinstance(field, dict):
                        raise ValueError("Saved Final Quality checklist is invalid.")
                    name = field.get("name")
                    if not isinstance(name, str) or "value" not in field:
                        raise ValueError("Saved Final Quality checklist is invalid.")
                    verify_fields[field_aliases.get(name, name)] = field["value"]
                data = verify_fields
            if (
                isinstance(data, dict)
                and row[1] is not None
                and not data.get("time_start")
            ):
                data = dict(data)
                data["time_start"] = (
                    row[1].isoformat()
                    if hasattr(row[1], "isoformat")
                    else str(row[1])
                )
            return data
        except mysql.connector.Error:
            return None


# ***************************************************Transition jobcards from 'Ready for Pickup' to 'Complete' Section ************************************
@anvil.server.callable()
def transitionreadyforpickuptocomplete():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_jobcarddetails
            SET Status = 'Complete'
            WHERE Status = 'Ready for Pickup'
        """
        cursor.execute(query)
    return "All 'Ready for Pickup' jobcards have been updated to 'Complete'."

__all__ = [
    'getJobCardInstructions',
    'getJobCardTechNotes',
    'getJobCardRow',
    'getJobCardRowWithClientID',
    'check_job_card_duplicate',
    'save_job_card_details',
    'getJobCardID',
    'getJobCardRef',
    'getQuotationInvoiceName',
    'get_all_jobcards_by_status',
    'getTechnicianJobCards',
    'getJobCardRefEditDetails',
    'getJobCardDetailsWithNameSearch',
    'getJobCardDetailsWithRefOrFullnameSearch',
    'update_job_card_details',
    'saveSignedJobCardDetails',
    'getCheckedInJobcards',
    'saveCancellationReason',
    'getCancelledJobcardReason',
    'getRegNoUsingStatus',
    'getWorkDoneInJobCard',
    'get_progress_tracker_data',
    'get_tech_notes_details_by_job_id',
    'fillTechNotesFormData',
    'downloadTechNotesPdfForm',
    'getTechNotes',
    'saveTecnicianDefectsAndRequestedParts',
    'getJobCardDefects',
    'getJobCardPricedDefects',
    'deleteDefects',
    'getRequestedParts',
    'getDefectsStaffAndSignature',
    'updateJobCardStatus',
    'saveWorkDoneInJobCard',
    'updateDefectsList',
    'transitionCheckedInToCreateQuote',
    'updateBlankDefectsAndRequestedParts',
    'getDefectsList',
    'get_defects_form_init_data',
    'saveConfirmationDetails',
    'getVerifyTaskChecklist',
    'transitionreadyforpickuptocomplete',
]

from . import BMALocal as _compatibility_facade
