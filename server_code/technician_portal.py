from ._common import *

# *************************************************** Self Service Portal - Technician Assigned Jobcards by Status Section ************************************


def _strip_html_lines(raw_text):
    """Strip HTML tags and normalize block boundaries into clean newline-separated lines."""
    if not raw_text:
        return ""
    text_with_breaks = re.sub(r'</(p|li|div|br)\s*>', '\n', str(raw_text), flags=re.IGNORECASE)
    text_with_breaks = re.sub(r'<br\s*/?>', '\n', text_with_breaks, flags=re.IGNORECASE)
    text_only = re.sub(r'<[^>]+>', '', text_with_breaks)
    lines = [line.strip() for line in text_only.splitlines() if line.strip()]
    return "\n".join(lines)


def _normalize_reg_no(reg_no):
    """Normalize a vehicle registration number for exact comparison (uppercase, no spaces/hyphens)."""
    if not isinstance(reg_no, str):
        raise ValueError("Please enter a valid vehicle registration number.")
    normalized = re.sub(r'[\s-]+', '', reg_no.strip()).upper()
    if not normalized or len(normalized) > 50:
        raise ValueError("Please enter a valid vehicle registration number.")
    return normalized


def _format_quantity(value):
    """Format numeric quantities cleanly (whole numbers without .0)."""
    if value is None:
        return ""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.2f}".rstrip("0").rstrip(".")


def _parse_checklist_fields_json(fields_raw):
    """Safely parse FieldsJSON from tbl_technicianinspectionchecklist."""
    if not fields_raw:
        return []
    if isinstance(fields_raw, (str, bytes)):
        try:
            parsed = json.loads(fields_raw)
        except (ValueError, TypeError):
            return []
    else:
        parsed = fields_raw

    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        return [{"name": k, "label": k, "value": v} for k, v in parsed.items()]
    return []


@anvil.server.callable()
def get_technician_jobcards_by_status():
    _get_current_user()
    with db_cursor() as cursor:
        jobs_query = """
            SELECT 
                tbl_jobcarddetails.ReceivedDate,
                tbl_technicians.Fullname,
                tbl_jobcarddetails.JobCardRef,
                tbl_jobcarddetails.ClientInstruction,
                tbl_jobcarddetails.Status
            FROM 
                tbl_pendingassignedjobs
            JOIN 
                tbl_jobcarddetails 
                ON tbl_pendingassignedjobs.JobCardRefID = tbl_jobcarddetails.ID
            JOIN 
                tbl_technicians
                ON tbl_pendingassignedjobs.TechnicianID = tbl_technicians.ID
            WHERE 
                tbl_jobcarddetails.Status IN ('Checked In', 'Create Quote', 'Confirm Quote', 'In Service')
            ORDER BY 
                tbl_jobcarddetails.ReceivedDate DESC;
        """
        cursor.execute(jobs_query)
        assigned_rows = cursor.fetchall()

        jobcards = []

        for i, row in enumerate(assigned_rows, start=1):
            received_date = row[0].strftime("%Y-%m-%d") if row[0] else ""
            technician = row[1]
            jobcarderef = row[2]
            formatted_instruction = _strip_html_lines(row[3])
            status_display = row[4]   # direct pass-through

            card = {
                "id": i,
                "ReceivedDate": received_date,
                "Technician": technician,
                "JobCardRef": str(jobcarderef),
                "Instruction": formatted_instruction,
                "status": status_display,
            }

            jobcards.append(card)

        return jobcards

# *************************************************** Self Service Portal - Technician Defects and Requested Parts Details Section ************************************
@anvil.server.callable()
def getExistingJobCardInDefectsAndRequestedParts(JobCardID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                ID 
            FROM 
                tbl_techniciandefectsandrequestedparts
            WHERE 
                JobCardRefID = %s     
        """
        cursor.execute(query, (JobCardID,))
        result = cursor.fetchone()
        return result[0] if result else None

@anvil.server.callable()
def saveOrUpdateTechnicianPortalDefectsAndRequestedParts(
    jobcardID,
    tech_notes,
    defects,
    requiredparts,
    staff,
    signature,
    checklist=None,
    inspection_images=None,
):
    _get_current_user()
    if checklist is not None and not isinstance(checklist, list):
        raise ValueError("Invalid vehicle inspection checklist.")
    if checklist:
        prepared_images = _prepare_vehicle_inspection_images(inspection_images)
    else:
        prepared_images = None

    checklist_rows = []
    if checklist:
        checklist_rows = [
            (
                jobcardID,
                str(entry.get("id", "")),
                str(entry.get("section", ""))[:1],
                str(entry.get("section_title", "")),
                str(entry.get("item", "")),
                1 if entry.get("checked") else 0,
                json.dumps(entry.get("fields") or []),
            )
            for entry in checklist
            if isinstance(entry, dict) and entry.get("id")
        ]

    new_image_paths = []
    replaced_image_paths = []
    try:
        image_rows = (
            _write_vehicle_inspection_images(
                jobcardID, prepared_images, new_image_paths
            )
            if checklist_rows
            else None
        )
        with db_cursor() as cursor:
            signature_bytes = signature.get_bytes() if signature else None
            cursor.execute(
                "UPDATE tbl_jobcarddetails SET Notes = %s WHERE ID = %s",
                (tech_notes, jobcardID),
            )
            cursor.execute(
                """
                SELECT ID
                FROM tbl_techniciandefectsandrequestedparts
                WHERE JobCardRefID = %s
                """,
                (jobcardID,),
            )
            existing_record = cursor.fetchone()

            if existing_record:
                cursor.execute(
                    """
                    UPDATE tbl_techniciandefectsandrequestedparts
                    SET Defects = %s, TechnicianPortalRequestedParts = %s,
                        PreparedByStaff = %s, Signature = %s
                    WHERE JobCardRefID = %s
                    """,
                    (defects, requiredparts, staff, signature_bytes, jobcardID),
                )
                _insert_technician_portal_notification(
                    cursor,
                    jobcardID,
                    "Technician Portal updates made under Checked In. Please review the changes.",
                )
            else:
                cursor.execute(
                    "UPDATE tbl_jobcarddetails SET Status = 'Create Quote' WHERE ID = %s",
                    (jobcardID,),
                )
                cursor.execute(
                    """
                    INSERT INTO tbl_techniciandefectsandrequestedparts
                        (JobCardRefID, Defects, PricedDefectsList,
                         TechnicianPortalRequestedParts, RequestedParts,
                         PreparedByStaff, Signature)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        jobcardID,
                        defects,
                        defects,
                        requiredparts,
                        requiredparts,
                        staff,
                        signature_bytes,
                    ),
                )
                _insert_technician_portal_notification(
                    cursor,
                    jobcardID,
                    "New Technician Portal entry made under Checked In. Please review the entry.",
                )

            if checklist_rows:
                cursor.executemany(
                    """
                    INSERT INTO tbl_technicianinspectionchecklist
                        (JobCardRefID, ItemCode, SectionCode, SectionTitle,
                         ItemDescription, IsChecked, FieldsJSON)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        SectionCode = VALUES(SectionCode),
                        SectionTitle = VALUES(SectionTitle),
                        ItemDescription = VALUES(ItemDescription),
                        IsChecked = VALUES(IsChecked),
                        FieldsJSON = VALUES(FieldsJSON),
                        UpdatedAt = CURRENT_TIMESTAMP
                    """,
                    checklist_rows,
                )
                replaced_image_paths = _upsert_vehicle_inspection_image_rows(
                    cursor, jobcardID, image_rows
                )
    except Exception:
        _remove_vehicle_inspection_images(new_image_paths)
        raise

    _remove_vehicle_inspection_images(replaced_image_paths)
    return True

        

@anvil.server.callable()
def get_jobcard_and_defect_details(jobcard_ref_str):
    """
    Joins job card details with technician defects and returns 
    data including a base64 encoded signature and saved inspection checklist.
    """
    _get_current_user()
    query = """
        SELECT 
            j.Notes, 
            t.Defects, 
            t.TechnicianPortalRequestedParts, 
            t.PreparedByStaff, 
            t.Signature,
            j.ID
        FROM tbl_jobcarddetails j
        JOIN tbl_techniciandefectsandrequestedparts t ON t.JobCardRefID = j.ID
        WHERE j.JobCardRef = %s
        ORDER BY t.ID DESC
    """
    
    checklist_items = []
    with db_cursor() as cursor:
        cursor.execute(query, (jobcard_ref_str,))
        results = cursor.fetchall()

        if results and len(results[0]) >= 6 and results[0][5] is not None:
            jobcard_id = results[0][5]
            try:
                cursor.execute(
                    """
                    SELECT ItemCode, SectionCode, SectionTitle, ItemDescription, IsChecked, FieldsJSON
                    FROM tbl_technicianinspectionchecklist
                    WHERE JobCardRefID = %s
                        AND SectionCode <> 'F'
                        AND ItemCode NOT LIKE %s
                    ORDER BY ID ASC
                    """,
                    (jobcard_id, _VEHICLE_INSPECTION_ITEM_CODE_PREFIX + "%"),
                )
                for cl_row in cursor.fetchall() or []:
                    item_code, sec_code, sec_title, item_desc, is_checked, fields_raw = cl_row
                    try:
                        parsed_fields = (
                            json.loads(fields_raw)
                            if isinstance(fields_raw, (str, bytes)) and fields_raw
                            else (fields_raw if isinstance(fields_raw, list) else [])
                        )
                    except Exception:
                        parsed_fields = []
                    checklist_items.append({
                        "id": item_code,
                        "section": sec_code,
                        "section_title": sec_title,
                        "item": item_desc,
                        "checked": bool(is_checked),
                        "fields": parsed_fields,
                    })
            except mysql.connector.Error:
                checklist_items = []

    formatted_data = []
    
    for row in results:
        notes, defects, parts, staff, sig_bytes = row[:5]
        
        # Convert blob signature to base64 string
        sig_base64 = None
        if sig_bytes:
            # We encode the bytes and decode to utf-8 to get a clean string
            sig_base64 = base64.b64encode(sig_bytes).decode('utf-8')
        
        if parts == "None":
            parts = ""

        formatted_data.append({
            "Notes": notes,
            "Defects": defects,
            "RequestedParts": parts,
            "PreparedByStaff": staff,
            "Signature": sig_base64,  # This is now a base64 string
            "Checklist": checklist_items,
        })

    return formatted_data
# *************************************************** Self Service Portal - Car Part Names and Categories Section ************************************
@anvil.server.callable()
def getCarPartNamesAndCategory():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT Name, Category, PartNo
            FROM tbl_carpartnames
            ORDER BY Category ASC, Name ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Use a list comprehension and direct indices for maximum speed
        return [
            {
                "Name": r[0], 
                "Category": r[1], 
                "PartNo": r[2]
            } 
            for r in rows
        ]
# *************************************************** Self Service Portal - List of Technicians for Dropdown Section ************************************
@anvil.server.callable()
def get_technicians_list():
    _get_current_user()
    with db_cursor() as cursor:
        # Use 'AS combined_name' to ensure both sides of the UNION have the same key
        query = """
                SELECT Staff AS combined_name FROM tbl_checkstaff WHERE IsArchived = FALSE
                UNION ALL
                SELECT Fullname AS combined_name FROM tbl_technicians WHERE IsArchived = FALSE
                ORDER BY combined_name ASC
            """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            # Handle both dictionary-style and tuple-style rows safely
            if isinstance(r, dict):
                name = r["combined_name"]
            else:
                # If you only SELECT combined_name, it will be at index 0
                name = r[0] 
                
            result.append({"Fullname": name})
        
        # Extract just the values into a flat list
        return [r["Fullname"] if isinstance(r, dict) else r[0] for r in rows]

# *************************************************** Self Service Portal - Customer Feedback And Approved Parts by Job Card Reference Section ************************************
@anvil.server.callable()
def get_parts_and_feedback_by_jobcardref(jobcard_ref):

    _get_current_user()
    with db_cursor() as cursor:
        query = """
        SELECT
            tbl_quotationpartsandservicesfeedback.Item,
            tbl_quotationpartsandservicesfeedback.QuantityIssued,
            tbl_clientquotationfeedback.Remarks
        FROM tbl_jobcarddetails
        INNER JOIN tbl_clientquotationfeedback
            ON tbl_jobcarddetails.ID = tbl_clientquotationfeedback.AssignedJobID
        INNER JOIN tbl_quotationpartsandservicesfeedback
            ON tbl_jobcarddetails.ID = tbl_quotationpartsandservicesfeedback.AssignedJobID
        WHERE tbl_jobcarddetails.JobCardRef = %s
          AND tbl_quotationpartsandservicesfeedback.Item <> 'Labour'
        ORDER BY tbl_quotationpartsandservicesfeedback.ID ASC
         """
        cursor.execute(query, (jobcard_ref,))
        rows = cursor.fetchall()

    # return as list of dicts (Anvil-friendly)
    return [
        {
            "Item": row[0],
            "QuantityIssued": row[1],
            "Remarks": row[2]
        }
        for row in rows
    ]

# *************************************************** Self Service Portal - Car Part Categories Update Section ************************************

# 1. Turn the actual work into a background task
@anvil.server.background_task
def update_carpart_taxonomy_bg(data_list):
    try:
        with db_cursor() as cursor:
            for row in data_list:
                category = row.get('Category')
                patterns = row.get('Patterns')
                
                sql = "UPDATE tbl_carpart_taxonomy SET Patterns = %s WHERE Category = %s"
                cursor.execute(sql, (patterns, category))
                
        # Re-run categorization
        updated_count = _update_carpart_categories(filter_mode="all")
        
        # You can optionally return data from a background task
        return f"Success: Updated taxonomy and categorized {updated_count} parts."
        
    except Exception as e:
        return f"Error saving data: {str(e)}"

# 2. Create a callable function that launches the background task
@anvil.server.callable()
def launch_taxonomy_update(data_list):
    # This launches the task and returns control to the client immediately
    task = anvil.server.launch_background_task('update_carpart_taxonomy_bg', data_list)
    return task
    
@anvil.server.callable()
def load_taxonomy():
    """Load taxonomy into a dict of {category: [patterns]}."""
    taxonomy = {}
    with db_cursor() as cursor:
        cursor.execute("SELECT Category, Patterns FROM tbl_carpart_taxonomy ORDER BY Category ASC")
        rows = cursor.fetchall()
        for category, pattern_str in rows:
            # split by comma, strip spaces
            patterns = [p.strip() for p in pattern_str.split(",") if p.strip()]
            taxonomy[category] = patterns
    
    return taxonomy


# -------------------------------
# Shared categorization function
# -------------------------------

# Pass the taxonomy in as a parameter so we don't fetch it every time
def strict_categorize(name: str, taxonomy: dict) -> str:
    name_l = str(name).lower()
    for category, patterns in taxonomy.items():
        for pat in patterns:
            if re.search(pat, name_l):  
                return category

    # fallback
    if "engine" in name_l:
        return "Engine Components"
    return "Engine Components"

def _update_carpart_categories(filter_mode: str = "all", params: tuple = ()):
    """Update car part categories based on a safe filter_mode.

    filter_mode: "all"  -> no WHERE clause (update every row)
                 "null" -> only rows where Category IS NULL
    """
    _ALLOWED_FILTERS = {
        "all":  "",
        "null": "WHERE tbl_carpartnames.Category IS NULL",
    }
    if filter_mode not in _ALLOWED_FILTERS:
        raise ValueError(f"Invalid filter_mode: {filter_mode!r}")

    where_clause = _ALLOWED_FILTERS[filter_mode]

    # 1. LOAD TAXONOMY EXACTLY ONCE
    taxonomy = load_taxonomy()

    with db_cursor() as cursor:
        select_sql = f"""
            SELECT ID, Name
            FROM tbl_carpartnames
            {where_clause}
        """
        cursor.execute(select_sql, params)
        rows = cursor.fetchall()

        # 2. CATEGORIZE IN MEMORY
        update_data = []
        for part_id, name in rows:
            category = strict_categorize(name, taxonomy)
            update_data.append((category, part_id)) # Add tuple to list

        # 3. BATCH UPDATE EVERYTHING AT ONCE
        if update_data:
            update_sql = """
                UPDATE tbl_carpartnames
                SET Category = %s
                WHERE ID = %s
            """
            cursor.executemany(update_sql, update_data)

        return len(update_data)
    
@anvil.server.callable()
def update_carpart_categories():
    updated_count = _update_carpart_categories(
        filter_mode="all"
    )

    return {
        "status": "ok",
        "updated_rows": updated_count
    }

@anvil.server.callable()
def update_null_carpart_categories():
    updated_count = _update_carpart_categories(
        filter_mode="null"
    )

    return {
        "status": "ok",
        "updated_null_rows": updated_count
    }


# *************************************************** Self Service Portal - Save Work Done by Technician Section ************************************
@anvil.server.callable()
def save_work_done_by_technician(jobcardref, work_done):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_jobcarddetails
            SET Status ="Verify Task"
            WHERE JobCardRef = %s
        """
        cursor.execute(query, ( jobcardref,))

    #Update work done in job card details
    jobcardid = getJobCardID(jobcardref)
    saveWorkDoneInJobCard(jobcardid, work_done)
    publish_realtime_event("jobcards", "work_done", entity_id=jobcardid)
    publish_realtime_event("technician_portal", "work_done", entity_id=jobcardid)

# *************************************************** Self Service Portal - Vehicle Service History Section ************************************
@anvil.server.callable()
def get_vehicle_service_history(reg_no):
    """
    Retrieve chronological service history for an exact normalized vehicle registration number.

    Excludes cancelled job cards, returns invoiced parts & services (without prices),
    defects, check-in notes, work done, mileage, next service mileage, and inspection flags.
    """
    _get_current_user()
    normalized_reg = _normalize_reg_no(reg_no)

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                j.ID,
                j.ReceivedDate,
                j.JobCardRef,
                j.RegNo,
                j.MakeAndModel,
                j.Mileage,
                j.ClientInstruction,
                j.Notes,
                j.Status,
                j.IsComplete
            FROM tbl_jobcarddetails j
            WHERE UPPER(REPLACE(REPLACE(TRIM(j.RegNo), ' ', ''), '-', '')) = %s
              AND (j.Status IS NULL OR j.Status <> 'Cancel Jobcard')
            ORDER BY j.ReceivedDate DESC, j.ID DESC
            LIMIT 200
            """,
            (normalized_reg,),
        )
        job_rows = cursor.fetchall() or []

        if not job_rows:
            return {
                "reg_no": normalized_reg,
                "make_and_model": "",
                "records": [],
            }

        job_ids = [row[0] for row in job_rows]
        placeholders = ", ".join(["%s"] * len(job_ids))
        id_params = tuple(job_ids)

        # 1. Assigned technicians
        technicians_by_job = {}
        cursor.execute(
            f"""
            SELECT p.JobCardRefID, t.Fullname
            FROM tbl_pendingassignedjobs p
            JOIN tbl_technicians t ON p.TechnicianID = t.ID
            WHERE p.JobCardRefID IN ({placeholders})
            ORDER BY p.ID DESC
            """,
            id_params,
        )
        for job_id, fullname in cursor.fetchall() or []:
            if fullname:
                names = technicians_by_job.setdefault(job_id, [])
                if fullname not in names:
                    names.append(fullname)

        # 2. Work done
        work_done_by_job = {}
        cursor.execute(
            f"""
            SELECT JobCardRefID, WorkDone
            FROM tbl_workdoneinjobcard
            WHERE JobCardRefID IN ({placeholders})
            ORDER BY ID ASC
            """,
            id_params,
        )
        for job_id, work_done in cursor.fetchall() or []:
            cleaned = _strip_html_lines(work_done)
            if cleaned:
                work_done_by_job.setdefault(job_id, []).append(cleaned)

        # 3. Technician defects
        defects_by_job = {}
        cursor.execute(
            f"""
            SELECT JobCardRefID, Defects
            FROM tbl_techniciandefectsandrequestedparts
            WHERE JobCardRefID IN ({placeholders})
            ORDER BY ID DESC
            """,
            id_params,
        )
        for job_id, defects in cursor.fetchall() or []:
            if job_id not in defects_by_job:
                cleaned = _strip_html_lines(defects)
                if cleaned:
                    defects_by_job[job_id] = cleaned

        # 4. Invoiced parts & services (strictly tbl_invoices, no prices/amounts)
        parts_by_job = {}
        cursor.execute(
            f"""
            SELECT AssignedJobID, Item, Part_No, QuantityIssued
            FROM tbl_invoices
            WHERE AssignedJobID IN ({placeholders})
            ORDER BY ID ASC
            """,
            id_params,
        )
        for job_id, item, part_no, qty in cursor.fetchall() or []:
            item_text = str(item or "").strip()
            if not item_text:
                continue
            parts_by_job.setdefault(job_id, []).append({
                "item": item_text,
                "part_no": str(part_no or "").strip(),
                "quantity": _format_quantity(qty),
            })

        # 5. Inspection checklist (next service mileage + presence flag)
        next_mileage_by_job = {}
        has_checklist_jobs = set()
        cursor.execute(
            f"""
            SELECT JobCardRefID, ItemCode, FieldsJSON
            FROM tbl_technicianinspectionchecklist
            WHERE JobCardRefID IN ({placeholders})
            ORDER BY ID ASC
            """,
            id_params,
        )
        for job_id, _item_code, fields_raw in cursor.fetchall() or []:
            has_checklist_jobs.add(job_id)
            if job_id not in next_mileage_by_job:
                for field in _parse_checklist_fields_json(fields_raw):
                    if field.get("name") == "txt_next_service_mileage":
                        val = str(field.get("value") or "").strip()
                        if val:
                            next_mileage_by_job[job_id] = val
                            break

        # 6. Inspection photos presence
        has_photos_jobs = set()
        cursor.execute(
            f"""
            SELECT DISTINCT JobCardRefID
            FROM tbl_vehicleinspectionimages
            WHERE JobCardRefID IN ({placeholders})
            """,
            id_params,
        )
        for (job_id,) in cursor.fetchall() or []:
            has_photos_jobs.add(job_id)

    make_and_model_summary = ""
    records = []
    for row in job_rows:
        (
            job_id,
            received_date,
            jobcard_ref,
            db_reg_no,
            make_and_model,
            mileage,
            client_instruction,
            notes,
            status,
            is_complete,
        ) = row

        make_text = str(make_and_model or "").strip()
        if make_text and not make_and_model_summary:
            make_and_model_summary = make_text

        date_str = (
            received_date.strftime("%Y-%m-%d")
            if hasattr(received_date, "strftime")
            else str(received_date or "")
        )

        if status:
            display_status = str(status)
        elif is_complete in (1, b"\x01", True):
            display_status = "Completed"
        else:
            display_status = "Historical"

        records.append({
            "jobcard_id": job_id,
            "date": date_str,
            "jobcard_ref": str(jobcard_ref or ""),
            "reg_no": str(db_reg_no or normalized_reg),
            "make_and_model": make_text,
            "status": display_status,
            "technician": ", ".join(technicians_by_job.get(job_id, [])),
            "mileage": mileage if mileage is not None else "",
            "next_service_mileage": next_mileage_by_job.get(job_id, ""),
            "client_instruction": _strip_html_lines(client_instruction),
            "notes": _strip_html_lines(notes),
            "defects": defects_by_job.get(job_id, ""),
            "work_done": "\n".join(work_done_by_job.get(job_id, [])),
            "parts_and_services": parts_by_job.get(job_id, []),
            "has_inspection": (job_id in has_checklist_jobs) or (job_id in has_photos_jobs),
        })

    return {
        "reg_no": normalized_reg,
        "make_and_model": make_and_model_summary,
        "records": records,
    }


@anvil.server.callable()
def get_service_history_inspection(jobcard_id):
    """
    Lazy-load saved vehicle inspection checklist findings and photos for a job card.
    """
    _get_current_user()
    if isinstance(jobcard_id, bool) or not isinstance(jobcard_id, int) or jobcard_id <= 0:
        raise ValueError("Invalid job card ID.")

    checklist_items = []
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ItemCode, SectionCode, SectionTitle, ItemDescription, IsChecked, FieldsJSON
            FROM tbl_technicianinspectionchecklist
            WHERE JobCardRefID = %s
            ORDER BY SectionCode ASC, ID ASC
            """,
            (jobcard_id,),
        )
        for item_code, sec_code, sec_title, item_desc, is_checked, fields_raw in cursor.fetchall() or []:
            checklist_items.append({
                "item_code": str(item_code or ""),
                "section_code": str(sec_code or ""),
                "section_title": str(sec_title or ""),
                "item_description": str(item_desc or ""),
                "is_checked": bool(is_checked),
                "fields": _parse_checklist_fields_json(fields_raw),
            })

    inspection_data = get_vehicle_inspection_data(jobcard_id)
    images = inspection_data.get("images", {}) if isinstance(inspection_data, dict) else {}

    return {
        "checklist": checklist_items,
        "images": {
            "image_1": images.get("image_1"),
            "image_2": images.get("image_2"),
            "image_3": images.get("image_3"),
        },
    }


@anvil.server.callable()
def get_self_service_bootstrap():
    """Combined single-round-trip bootstrap for SelfService (Technician Portal)."""
    _get_current_user()
    return {
        "parts_taxonomy": getCarPartNamesAndCategory(),
        "jobcards_by_status": get_technician_jobcards_by_status(),
        "technicians": get_technicians_list(),
    }


@anvil.server.callable()
def get_vehicle_inspection_by_ref(jobcard_ref):
    """Resolve jobcard_ref and return its vehicle inspection data in one round-trip."""
    _get_current_user()
    if not jobcard_ref or not str(jobcard_ref).strip():
        raise ValueError("Invalid jobcard_ref provided.")
    jobcard_id = getJobCardID(jobcard_ref)
    if not jobcard_id:
        return None
    return get_vehicle_inspection_data(jobcard_id)


__all__ = [
    'get_technician_jobcards_by_status',
    'getExistingJobCardInDefectsAndRequestedParts',
    'saveOrUpdateTechnicianPortalDefectsAndRequestedParts',
    'get_jobcard_and_defect_details',
    'getCarPartNamesAndCategory',
    'get_technicians_list',
    'get_parts_and_feedback_by_jobcardref',
    'update_carpart_taxonomy_bg',
    'launch_taxonomy_update',
    'load_taxonomy',
    'strict_categorize',
    '_update_carpart_categories',
    'update_carpart_categories',
    'update_null_carpart_categories',
    'save_work_done_by_technician',
    'get_vehicle_service_history',
    'get_service_history_inspection',
    'get_self_service_bootstrap',
    'get_vehicle_inspection_by_ref',
]

from . import BMALocal as _compatibility_facade
