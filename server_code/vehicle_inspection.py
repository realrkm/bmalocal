from ._common import *

#*************************************************** Save Or Update Vehicle Inspection Section ************************************
_VEHICLE_INSPECTION_SECTIONS = (
    (
        "A",
        ("A1", "chk_safety"),
        (
            ("A2", "chk_jack"),
            ("A3", "chk_chock"),
            ("A4", "chk_ppe"),
            ("A5", "chk_valuables"),
        ),
        (),
    ),
    (
        "B",
        ("B1", "chk_complain"),
        (("B2", "chk_test_drive"), ("B3", "chk_scan")),
        (
            "text_box_test_drive",
            "text_box_fault_code",
            "text_box_faults_cleared",
        ),
    ),
    (
        "C",
        ("C1", "chk_service"),
        (
            ("C2", "chk_oil_level"),
            ("C3", "chk_oil_filter"),
            ("C4", "chk_air_filter"),
            ("C5", "chk_coolant"),
            ("C6", "chk_belt"),
            ("C7", "chk_battery"),
        ),
        ("text_box_cracks", "text_box_voltage", "text_box_cca"),
    ),
    (
        "D",
        ("D1", "chk_carriage"),
        (
            ("D2", "chk_front_arms"),
            ("D3", "chk_rear_diff"),
            ("D4", "chk_shocks"),
            ("D5", "chk_exhaust"),
            ("D6", "chk_shaft"),
            ("D7", "chk_oil_leaks"),
        ),
        (
            "text_box_any_play",
            "text_box_any_issue",
            "text_box_broken",
            "text_box_rattles",
            "text_box_vibration",
            "text_box_oil_leaks",
        ),
    ),
    (
        "E",
        ("E1", "chk_brakes"),
        (
            ("E2", "chk_front_pads"),
            ("E3", "chk_rear_pads"),
            ("E4", "chk_brake_fluid"),
            ("E5", "chk_tyre_pressure"),
        ),
        (
            "text_box_front_pad_thickness",
            "text_box_front_disc",
            "text_box_rear_pad_thickness",
            "text_box_17",
            "text_box_18",
            "text_box_22",
            "text_box_tyre_tread",
        ),
    ),
    (
        "F",
        ("F1", "chk_final"),
        (
            ("F2", "chk_torque"),
            ("F3", "chk_road_test"),
            ("F4", "chk_engine_clean"),
            ("F5", "chk_old_parts"),
            ("F6", "chk_invoice_explain"),
        ),
        (
            "txt_next_service_mileage",
            "txt_efficiency",
            "date_picker_next_service",
            "date_picker_time_start",
            "date_picker_time_end",
        ),
    ),
)
_VEHICLE_INSPECTION_CHECKBOXES = tuple(
    component_name
    for _, header, items, _ in _VEHICLE_INSPECTION_SECTIONS
    for _, component_name in (header,) + items
)
_VEHICLE_INSPECTION_TEXTBOXES = (
    "text_box_test_drive",
    "text_box_fault_code",
    "text_box_faults_cleared",
    "text_box_cracks",
    "text_box_voltage",
    "text_box_cca",
    "text_box_any_play",
    "text_box_any_issue",
    "text_box_broken",
    "text_box_rattles",
    "text_box_vibration",
    "text_box_oil_leaks",
    "text_box_front_pad_thickness",
    "text_box_front_disc",
    "text_box_rear_pad_thickness",
    "text_box_17",
    "text_box_18",
    "text_box_22",
    "text_box_tyre_tread",
    "txt_next_service_mileage",
    "txt_efficiency",
)
_VEHICLE_INSPECTION_DATES = (
    "date_picker_next_service",
    "date_picker_time_start",
    "date_picker_time_end",
)
_VEHICLE_INSPECTION_PDF_FIELD_LABELS = {
    "chk_final": "Final Quality and Handover",
    "chk_torque": "Torque: Wheels 140Nm, Oil drain 25Nm, Filter housing 25Nm",
    "chk_road_test": "Road test 5km - No warning lights, no noise, ISTA no faults",
    "chk_engine_clean": "Engine bay cleaned, car washed, vacuumed",
    "chk_old_parts": "Old parts in boot - Shown to customer",
    "chk_invoice_explain": "Invoice explained",
    "text_box_test_drive": "Any Noise/vibration confirmed?",
    "text_box_fault_code": "Fault codes",
    "text_box_faults_cleared": "Faults cleared after",
    "text_box_cracks": "Any Cracks / Leaks?",
    "text_box_voltage": "Voltage",
    "text_box_cca": "CCA",
    "text_box_any_play": "Any play on Front control arms/bushes or ball joints?",
    "text_box_any_issue": "Any issue on rear diff bush or subframe bushes?",
    "text_box_broken": "Any leaks / broken shock absorbers or springs?",
    "text_box_rattles": "Any rattles on exhaust mounts or heat shields?",
    "text_box_vibration": "Any vibration on proptshaft guibo or center bearing?",
    "text_box_oil_leaks": "Any Oil Leaks?",
    "text_box_front_pad_thickness": "Front pads thickness (Min 3 mm)",
    "text_box_front_disc": "Front discs sizes (mm)",
    "text_box_rear_pad_thickness": "Rear pads sizes (mm)",
    "text_box_17": "Rear disc thickness (mm)",
    "text_box_18": "Front tyre pressure (psi)",
    "text_box_22": "Rear tyre pressure (psi)",
    "text_box_tyre_tread": "Tyre Tread (mm)",
    "txt_next_service_mileage": "Enter Next Service Mileage",
    "txt_efficiency": "Efficiency:",
    "date_picker_next_service": "Next Service Date",
    "date_picker_time_start": "Time started:",
    "date_picker_time_end": "Time finished:",
}
_VEHICLE_INSPECTION_IMAGES = ("image_1", "image_2", "image_3")
_VEHICLE_INSPECTION_ITEM_CODE_PREFIX = "V-"
_SELF_SERVICE_INSPECTION_CHECKBOX_COMPONENTS = {
    "A1": "chk_jack",
    "A2": "chk_chock",
    "A3": "chk_ppe",
    "A4": "chk_valuables",
    "B1": "chk_test_drive",
    "B2": "chk_scan",
    "C1": "chk_oil_level",
    "C2": "chk_oil_filter",
    "C3": "chk_air_filter",
    "C4": "chk_coolant",
    "C5": "chk_belt",
    "C6": "chk_battery",
    "D1": "chk_front_arms",
    "D2": "chk_rear_diff",
    "D3": "chk_shocks",
    "D4": "chk_exhaust",
    "D5": "chk_shaft",
    "D6": "chk_oil_leaks",
    "E1": "chk_front_pads",
    "E2": "chk_rear_pads",
    "E3": "chk_brake_fluid",
    "E4": "chk_tyre_pressure",
}
_SELF_SERVICE_INSPECTION_FIELD_COMPONENTS = {
    "noise": "text_box_test_drive",
    "codes": "text_box_fault_code",
    "cleared": "text_box_faults_cleared",
    "belts": "text_box_cracks",
    "volts": "text_box_voltage",
    "cca": "text_box_cca",
    "arms": "text_box_any_play",
    "reardiff": "text_box_any_issue",
    "shocks": "text_box_broken",
    "exhaust": "text_box_rattles",
    "propshaft": "text_box_vibration",
    "leaks": "text_box_oil_leaks",
    "fpad": "text_box_front_pad_thickness",
    "fdisc": "text_box_front_disc",
    "rpad": "text_box_rear_pad_thickness",
    "rdisc": "text_box_17",
    "pf": "text_box_18",
    "pr": "text_box_22",
    "tread": "text_box_tyre_tread",
}
_SELF_SERVICE_INSPECTION_SECTION_ITEMS = {
    "A": ("A1", "A2", "A3", "A4"),
    "B": ("B1", "B2"),
    "C": ("C1", "C2", "C3", "C4", "C5", "C6"),
    "D": ("D1", "D2", "D3", "D4", "D5", "D6"),
    "E": ("E1", "E2", "E3", "E4"),
}
_SELF_SERVICE_INSPECTION_SECTION_CHECKBOXES = {
    "A": "chk_safety",
    "B": "chk_complain",
    "C": "chk_service",
    "D": "chk_carriage",
    "E": "chk_brakes",
}
_VEHICLE_INSPECTION_IMAGE_TYPES = {
    "image/jpeg": (".jpg", lambda content: content.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda content: content.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (
        ".webp",
        lambda content: (
            len(content) >= 12
            and content[:4] == b"RIFF"
            and content[8:12] == b"WEBP"
        ),
    ),
}
_MAX_VEHICLE_INSPECTION_IMAGE_BYTES = 10 * 1024 * 1024


def _validate_vehicle_inspection_data(jobcard_id, data_dict):
    if type(jobcard_id) is not int or jobcard_id <= 0:
        raise ValueError("Invalid job card ID.")
    if not isinstance(data_dict, dict):
        raise ValueError("Invalid inspection checklist data.")

    required_keys = {"checkboxes", "textboxes", "dates", "images", "labels"}
    if set(data_dict) != required_keys:
        raise ValueError("Inspection checklist data is incomplete.")

    checkboxes = data_dict["checkboxes"]
    textboxes = data_dict["textboxes"]
    dates = data_dict["dates"]
    images = data_dict["images"]
    labels = data_dict["labels"]
    if not all(
        isinstance(value, dict)
        for value in (checkboxes, textboxes, dates, images, labels)
    ):
        raise ValueError("Invalid inspection checklist components.")
    if set(checkboxes) != set(_VEHICLE_INSPECTION_CHECKBOXES):
        raise ValueError("Inspection checklist checkboxes are incomplete.")
    if set(textboxes) != set(_VEHICLE_INSPECTION_TEXTBOXES):
        raise ValueError("Inspection checklist text boxes are incomplete.")
    if set(dates) != set(_VEHICLE_INSPECTION_DATES):
        raise ValueError("Inspection checklist dates are incomplete.")
    if set(images) != set(_VEHICLE_INSPECTION_IMAGES):
        raise ValueError("Inspection checklist photos are incomplete.")

    unchecked = [name for name, checked in checkboxes.items() if checked is not True]
    if unchecked:
        raise ValueError("All inspection checkboxes must be checked.")

    for name, value in textboxes.items():
        if not isinstance(value, str) or not value.strip() or len(value) > 2000:
            raise ValueError("Invalid or blank inspection field: " + name)

    for name, value in dates.items():
        if not isinstance(value, str):
            raise ValueError("Invalid inspection date: " + name)
        try:
            if "T" in value:
                if datetime.datetime.fromisoformat(value).isoformat() != value:
                    raise ValueError
            elif datetime.date.fromisoformat(value).isoformat() != value:
                raise ValueError
        except ValueError:
            raise ValueError("Invalid inspection date: " + name)

    expected_labels = set(
        _VEHICLE_INSPECTION_CHECKBOXES
        + _VEHICLE_INSPECTION_TEXTBOXES
        + _VEHICLE_INSPECTION_DATES
    )
    if set(labels) != expected_labels:
        raise ValueError("Inspection checklist labels are incomplete.")
    for name, label in labels.items():
        if not isinstance(label, str) or not label.strip() or len(label) > 255:
            raise ValueError("Invalid inspection checklist label: " + name)

    prepared_images = _prepare_vehicle_inspection_images(images)

    return checkboxes, textboxes, dates, prepared_images, labels


def _prepare_vehicle_inspection_images(images):
    if not isinstance(images, dict) or set(images) != set(_VEHICLE_INSPECTION_IMAGES):
        raise ValueError("All three inspection photos are required.")

    prepared_images = {}
    for image_code, media in images.items():
        content_type = getattr(media, "content_type", None)
        media_type = _VEHICLE_INSPECTION_IMAGE_TYPES.get(content_type)
        get_bytes = getattr(media, "get_bytes", None)
        if media_type is None or not callable(get_bytes):
            raise ValueError("Unsupported inspection photo format.")
        image_bytes = get_bytes()
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise ValueError("Invalid inspection photo data.")
        image_bytes = bytes(image_bytes)
        extension, matches_signature = media_type
        if (
            not image_bytes
            or len(image_bytes) > _MAX_VEHICLE_INSPECTION_IMAGE_BYTES
            or not matches_signature(image_bytes)
        ):
            raise ValueError("Invalid or oversized inspection photo.")
        prepared_images[image_code] = (extension, image_bytes)

    return prepared_images


def _is_vehicle_inspection_image_path(path):
    if not isinstance(path, str) or not path:
        return False
    try:
        return os.path.dirname(os.path.abspath(path)) == os.path.abspath(
            VEHICLE_INSPECTION_IMAGE_DIR
        )
    except (OSError, ValueError):
        return False


def _write_vehicle_inspection_images(jobcard_id, prepared_images, new_image_paths):
    image_dir = os.path.abspath(VEHICLE_INSPECTION_IMAGE_DIR)
    os.makedirs(image_dir, exist_ok=True)
    image_rows = []
    for image_code in _VEHICLE_INSPECTION_IMAGES:
        extension, image_bytes = prepared_images[image_code]
        image_path = os.path.join(image_dir, uuid.uuid4().hex + extension)
        with open(image_path, "xb") as image_file:
            new_image_paths.append(image_path)
            image_file.write(image_bytes)
        image_rows.append((jobcard_id, image_code, image_path))
    return image_rows


def _upsert_vehicle_inspection_image_rows(cursor, jobcard_id, image_rows):
    cursor.execute(
        """
        SELECT ImagePath
        FROM tbl_vehicleinspectionimages
        WHERE JobCardRefID = %s
        """,
        (jobcard_id,),
    )
    replaced_image_paths = [
        row[0]
        for row in (cursor.fetchall() or [])
        if row and _is_vehicle_inspection_image_path(row[0])
    ]

    cursor.executemany(
        """
        INSERT INTO tbl_vehicleinspectionimages
            (JobCardRefID, ImageCode, ImagePath)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            ImagePath = VALUES(ImagePath),
            UpdatedAt = CURRENT_TIMESTAMP
        """,
        image_rows,
    )
    return replaced_image_paths


def _persist_vehicle_inspection_images(
    cursor, jobcard_id, prepared_images, new_image_paths
):
    image_rows = _write_vehicle_inspection_images(
        jobcard_id, prepared_images, new_image_paths
    )
    return _upsert_vehicle_inspection_image_rows(cursor, jobcard_id, image_rows)


def _remove_vehicle_inspection_images(image_paths):
    for image_path in image_paths:
        try:
            os.remove(image_path)
        except FileNotFoundError:
            pass
        except OSError:
            logging.exception("Could not remove a vehicle inspection image.")


@anvil.server.callable()
def save_update_vehicle_inspection(jobcard_id, data_dict):
    _get_current_user()
    checkboxes, textboxes, dates, prepared_images, labels = (
        _validate_vehicle_inspection_data(jobcard_id, data_dict)
    )

    checklist_rows = []
    for section_code, header, items, section_fields in _VEHICLE_INSPECTION_SECTIONS:
        item_code, header_name = header
        section_title = labels[header_name]
        fields_json = (
            json.dumps(
                [
                    {
                        "name": name,
                        "label": labels[name],
                        "value": (
                            textboxes[name] if name in textboxes else dates[name]
                        ),
                    }
                    for name in section_fields
                ]
            )
            if section_fields
            else None
        )
        checklist_rows.append(
            (
                jobcard_id,
                _VEHICLE_INSPECTION_ITEM_CODE_PREFIX + item_code,
                section_code,
                section_title,
                section_title,
                1 if checkboxes[header_name] else 0,
                fields_json,
            )
        )
        for item_code, component_name in items:
            checklist_rows.append(
                (
                    jobcard_id,
                    _VEHICLE_INSPECTION_ITEM_CODE_PREFIX + item_code,
                    section_code,
                    section_title,
                    labels[component_name],
                    1 if checkboxes[component_name] else 0,
                    None,
                )
            )

    new_image_paths = []
    replaced_image_paths = []
    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT ID FROM tbl_jobcarddetails WHERE ID = %s",
                (jobcard_id,),
            )
            if cursor.fetchone() is None:
                raise ValueError("The specified job card does not exist.")
            cursor.executemany(
                """
                INSERT INTO tbl_technicianinspectionchecklist
                    (JobCardRefID, ItemCode, SectionCode, SectionTitle, ItemDescription,
                     IsChecked, FieldsJSON)
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
            replaced_image_paths = _persist_vehicle_inspection_images(
                cursor, jobcard_id, prepared_images, new_image_paths
            )
    except Exception:
        _remove_vehicle_inspection_images(new_image_paths)
        raise

    _remove_vehicle_inspection_images(replaced_image_paths)

    return {"success": True, "jobcard_id": jobcard_id}

@anvil.server.callable()
def get_vehicle_inspection_data(jobcard_id):
    _get_current_user()
    if type(jobcard_id) is not int or jobcard_id <= 0:
        raise ValueError("Invalid job card ID.")

    checkboxes = {name: False for name in _VEHICLE_INSPECTION_CHECKBOXES}
    textboxes = {name: "" for name in _VEHICLE_INSPECTION_TEXTBOXES}
    dates = {name: None for name in _VEHICLE_INSPECTION_DATES}
    images = {name: None for name in _VEHICLE_INSPECTION_IMAGES}
    labels = {
        name: name.replace("_", " ").replace("chk ", "", 1).title()
        for name in (
            _VEHICLE_INSPECTION_CHECKBOXES
            + _VEHICLE_INSPECTION_TEXTBOXES
            + _VEHICLE_INSPECTION_DATES
        )
    }
    item_code_to_checkbox = {}
    for section_code, header, items, _ in _VEHICLE_INSPECTION_SECTIONS:
        item_code, component_name = header
        item_code_to_checkbox[_VEHICLE_INSPECTION_ITEM_CODE_PREFIX + item_code] = (
            component_name
        )
        if section_code == "F":
            item_code_to_checkbox[item_code] = component_name
        for item_code, component_name in items:
            item_code_to_checkbox[
                _VEHICLE_INSPECTION_ITEM_CODE_PREFIX + item_code
            ] = component_name
            if section_code == "F":
                item_code_to_checkbox[item_code] = component_name

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                EXISTS(
                    SELECT 1
                    FROM tbl_technicianinspectionchecklist
                    WHERE JobCardRefID = %s
                ),
                EXISTS(
                    SELECT 1
                    FROM tbl_vehicleinspectionimages
                    WHERE JobCardRefID = %s
                )
            """,
            (jobcard_id, jobcard_id),
        )
        inspection_rows_exist = cursor.fetchone()
        if inspection_rows_exist is None:
            raise RuntimeError("Could not verify saved vehicle inspection data.")

        checklist_rows = []
        if inspection_rows_exist[0]:
            cursor.execute(
                """
                SELECT ItemCode, IsChecked, FieldsJSON, UpdatedAt,
                       SectionTitle, ItemDescription
                FROM tbl_technicianinspectionchecklist
                WHERE JobCardRefID = %s
                ORDER BY ItemCode
                """,
                (jobcard_id,),
            )
            checklist_rows = cursor.fetchall() or []

        image_rows = []
        if inspection_rows_exist[1]:
            cursor.execute(
                """
                SELECT ImageCode, ImagePath
                FROM tbl_vehicleinspectionimages
                WHERE JobCardRefID = %s
                ORDER BY ImageCode
                """,
                (jobcard_id,),
            )
            image_rows = cursor.fetchall() or []

    self_service_item_codes = set(_SELF_SERVICE_INSPECTION_CHECKBOX_COMPONENTS)
    self_service_rows_exist = any(
        row[0] in self_service_item_codes for row in checklist_rows
    )
    self_service_updated_at = [
        row[3]
        for row in checklist_rows
        if row[0] in self_service_item_codes and row[3] is not None
    ]
    legacy_updated_at = [
        row[3]
        for row in checklist_rows
        if str(row[0]).startswith(_VEHICLE_INSPECTION_ITEM_CODE_PREFIX)
        and row[3] is not None
    ]
    use_self_service_rows = self_service_rows_exist and (
        not legacy_updated_at
        or (
            bool(self_service_updated_at)
            and max(self_service_updated_at) >= max(legacy_updated_at)
        )
    )
    self_service_rows = []
    for (
        item_code,
        is_checked,
        fields_json,
        _updated_at,
        section_title,
        item_description,
    ) in sorted(
        checklist_rows,
        key=lambda row: (
            row[0] in self_service_item_codes,
            row[3] is not None,
            row[3],
        ),
    ):
        is_self_service_row = item_code in self_service_item_codes
        if is_self_service_row:
            if not use_self_service_rows:
                continue
            component_name = _SELF_SERVICE_INSPECTION_CHECKBOX_COMPONENTS[item_code]
            self_service_rows.append((item_code, bool(is_checked)))
        else:
            component_name = item_code_to_checkbox.get(item_code)
        if (
            component_name is None
            and not str(item_code).startswith(_VEHICLE_INSPECTION_ITEM_CODE_PREFIX)
        ):
            continue
        if component_name:
            checkboxes[component_name] = bool(is_checked)
            labels[component_name] = (
                item_description or section_title or labels[component_name]
            )
        if fields_json is None:
            continue
        if isinstance(fields_json, (str, bytes, bytearray)):
            try:
                fields_json = json.loads(fields_json)
            except (TypeError, ValueError) as error:
                raise ValueError("Saved inspection fields are invalid.") from error
        if isinstance(fields_json, dict):
            field_aliases = {
                "next_service_date": "date_picker_next_service",
                "next_service_mileage": "txt_next_service_mileage",
                "time_start": "date_picker_time_start",
                "time_end": "date_picker_time_end",
                "efficiency": "txt_efficiency",
                "chk_test": "chk_road_test",
                "chk_clean": "chk_engine_clean",
                "chk_old": "chk_old_parts",
                "chk_explain": "chk_invoice_explain",
            }
            fields_json = [
                {"name": field_aliases.get(name, name), "value": value}
                for name, value in fields_json.items()
            ]
        if not isinstance(fields_json, list):
            raise ValueError("Saved inspection fields are invalid.")
        for field in fields_json:
            if not isinstance(field, dict):
                raise ValueError("Saved inspection fields are invalid.")
            name = field.get("name")
            value = field.get("value")
            if is_self_service_row:
                field_label = field.get("label")
                name = _SELF_SERVICE_INSPECTION_FIELD_COMPONENTS.get(name)
            else:
                field_label = field.get("label")
                name = {
                    "chk_test": "chk_road_test",
                    "chk_clean": "chk_engine_clean",
                    "chk_old": "chk_old_parts",
                    "chk_explain": "chk_invoice_explain",
                }.get(name, name)
            if name in labels and isinstance(field_label, str) and field_label.strip():
                labels[name] = field_label
            if name in checkboxes:
                if type(value) is not bool:
                    raise ValueError("Saved inspection checkbox is invalid.")
                checkboxes[name] = value
            elif name in textboxes:
                textboxes[name] = "" if value is None else str(value)
            elif name in dates:
                dates[name] = None if value is None else str(value)

    latest_checklist_update = max(
        (row[3] for row in checklist_rows if row[3] is not None),
        default=None,
    )
    if latest_checklist_update is not None and dates["date_picker_time_start"] is None:
        dates["date_picker_time_start"] = (
            latest_checklist_update.isoformat()
            if hasattr(latest_checklist_update, "isoformat")
            else str(latest_checklist_update)
        )

    self_service_row_codes = {item_code for item_code, _ in self_service_rows}
    for section_code in {
        item_code[:1] for item_code in self_service_row_codes
    }:
        section_items = _SELF_SERVICE_INSPECTION_SECTION_ITEMS[section_code]
        for item_code in section_items:
            component_name = _SELF_SERVICE_INSPECTION_CHECKBOX_COMPONENTS[item_code]
            if item_code not in self_service_row_codes:
                checkboxes[component_name] = False
        checkboxes[_SELF_SERVICE_INSPECTION_SECTION_CHECKBOXES[section_code]] = all(
            checkboxes[_SELF_SERVICE_INSPECTION_CHECKBOX_COMPONENTS[item_code]]
            for item_code in section_items
        )

    image_directory = os.path.realpath(VEHICLE_INSPECTION_IMAGE_DIR)
    for image_code, image_path in image_rows:
        if image_code not in images:
            continue
        resolved_path = os.path.realpath(image_path)
        if os.path.dirname(resolved_path) != image_directory:
            raise ValueError("A saved inspection photo has an invalid path.")
        try:
            image_size = os.path.getsize(resolved_path)
            if image_size <= 0 or image_size > _MAX_VEHICLE_INSPECTION_IMAGE_BYTES:
                raise ValueError("A saved inspection photo is invalid or oversized.")
            with open(resolved_path, "rb") as image_file:
                image_bytes = image_file.read(_MAX_VEHICLE_INSPECTION_IMAGE_BYTES + 1)
        except OSError as error:
            logging.exception("Could not read a saved vehicle inspection image.")
            raise ValueError("A saved inspection photo could not be loaded.") from error
        if not image_bytes or len(image_bytes) > _MAX_VEHICLE_INSPECTION_IMAGE_BYTES:
            raise ValueError("A saved inspection photo is invalid or oversized.")

        extension = os.path.splitext(resolved_path)[1].lower()
        content_type = next(
            (
                mime_type
                for mime_type, (allowed_extension, matches_signature)
                in _VEHICLE_INSPECTION_IMAGE_TYPES.items()
                if extension == allowed_extension and matches_signature(image_bytes)
            ),
            None,
        )
        if content_type is None:
            raise ValueError("A saved inspection photo has an unsupported format.")
        images[image_code] = anvil.BlobMedia(
            content_type,
            image_bytes,
            name=os.path.basename(resolved_path),
        )

    return {
        "checkboxes": checkboxes,
        "textboxes": textboxes,
        "dates": dates,
        "images": images,
        "labels": labels,
    }


@anvil.server.callable()
def get_inspection_checklist_data_by_job_id(jobCardID):
    _get_current_user()
    if type(jobCardID) is not int or jobCardID <= 0:
        raise ValueError("Invalid job card ID.")
    return _get_inspection_checklist_data(jobCardID)

def _get_inspection_checklist_data(jobCardID):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                j.ID,
                j.JobCardRef,
                c.Fullname,
                j.RegNo,
                j.MakeAndModel,
                j.EngineCode,
                j.ChassisNo,
                j.EngineNo,
                j.Mileage,
                j.ReceivedDate
            FROM tbl_jobcarddetails AS j
            LEFT JOIN tbl_clientcontacts AS c ON c.ID = j.ClientDetails
            WHERE j.ID = %s
            """,
            (jobCardID,),
        )
        jobcard_row = cursor.fetchone()

    if jobcard_row is None:
        raise ValueError("The specified job card does not exist.")

    jobcard = {
        "ID": jobcard_row[0],
        "JobCardRef": jobcard_row[1],
        "ClientName": jobcard_row[2],
        "RegNo": jobcard_row[3],
        "MakeAndModel": jobcard_row[4],
        "EngineCode": jobcard_row[5],
        "ChassisNo": jobcard_row[6],
        "EngineNo": jobcard_row[7],
        "Mileage": jobcard_row[8],
        "ReceivedDate": jobcard_row[9],
    }
    return {
        "jobcard": jobcard,
        **get_vehicle_inspection_data(jobCardID),
    }



@anvil.server.callable()
def fillInspectionChecklistData(
    jobCardID,
    docType,
    logo_path: str = os.getenv("LOGO"),
    font_path: str = os.getenv("FONT_PATH"),
) -> str:

    _get_current_user()

    if type(jobCardID) is not int or jobCardID <= 0:
        raise ValueError("Invalid job card ID.")

    if docType != "InspectionChecklist":
        raise ValueError("Unsupported inspection checklist document type.")

    # ==========================================================
    # FETCH INSPECTION CHECKLIST DATA
    # ==========================================================

    data = _get_inspection_checklist_data(jobCardID)

    jobcard = data["jobcard"]
    checkboxes = data["checkboxes"]
    textboxes = data["textboxes"]
    dates = data["dates"]
    images = data["images"]
    labels = data.get("labels", {})

    # ==========================================================
    # HTML ESCAPING
    # ==========================================================

    def escaped(value):
        if value is None or value == "":
            return "&mdash;"

        if isinstance(value, (datetime.date, datetime.datetime)):
            value = value.isoformat()

        return html_module.escape(str(value)).replace("\n", "<br>")

    # ==========================================================
    # COMPANY LOGO
    # Same dimensions and styling as fillTechNotesFormData
    # ==========================================================

    logo_html = "LOGO"

    if logo_path and os.path.isfile(logo_path):

        logo_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(os.path.splitext(logo_path)[1].lower())

        if logo_type:

            with open(logo_path, "rb") as logo_file:
                logo_data = base64.b64encode(
                    logo_file.read()
                ).decode("ascii")

            logo_html = (
                '<img src="data:{};base64,{}" '
                'alt="Company Logo" '
                'style="width:100%;height:100%;'
                'object-fit:contain;border-radius:2px;">'
            ).format(logo_type, logo_data)

    # ==========================================================
    # MOZILLA HEADLINE FONT
    # Same font embedding as fillTechNotesFormData
    # ==========================================================

    font_base64 = ""

    if font_path and os.path.isfile(font_path):

        with open(font_path, "rb") as font_file:
            font_base64 = base64.b64encode(
                font_file.read()
            ).decode("ascii")

    font_face = ""

    if font_base64:

        font_face = """
            @font-face {{
                font-family: 'Mozilla Headline';
                src: url(data:font/ttf;base64,{})
                     format('truetype');
                font-weight: normal;
                font-style: normal;
            }}
        """.format(font_base64)

    # ==========================================================
    # CHECKBOX GRAPHICS
    # Drawn as inline SVG so wkhtmltopdf does not depend on a
    # font containing the ballot-box glyphs (U+2610 / U+2611).
    # ==========================================================

    checked_svg = (
        '<svg width="16" height="16" viewBox="0 0 16 16" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<rect x="0.5" y="0.5" width="15" height="15" fill="#fff" '
        'stroke="#000" stroke-width="1"/>'
        '<path d="M3.5 8.5 L6.5 11.5 L12.5 4.5" fill="none" '
        'stroke="#000" stroke-width="2"/>'
        '</svg>'
    )

    unchecked_svg = (
        '<svg width="16" height="16" viewBox="0 0 16 16" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<rect x="0.5" y="0.5" width="15" height="15" fill="#fff" '
        'stroke="#000" stroke-width="1"/>'
        '</svg>'
    )

    # ==========================================================
    # CHECKLIST ROWS
    # ==========================================================

    def checklist_row(component_name):

        symbol = (
            checked_svg
            if checkboxes.get(component_name) is True
            else unchecked_svg
        )

        label = (
            _VEHICLE_INSPECTION_PDF_FIELD_LABELS.get(component_name)
            or labels.get(component_name)
            or component_name.replace("_", " ").title()
        )

        return '<tr><td class="check">{}</td><td>{}</td></tr>'.format(
            symbol,
            escaped(label)
        )

    # ==========================================================
    # GENERATE CHECKLIST SECTIONS
    # ==========================================================

    checklist_sections = []

    for section_code, header, items, _section_fields in _VEHICLE_INSPECTION_SECTIONS:

        _item_code, header_name = header

        section_title = (
            _VEHICLE_INSPECTION_PDF_FIELD_LABELS.get(header_name)
            or labels.get(header_name)
            or "Section {}".format(section_code)
        )

        rows = [
            checklist_row(name)
            for _code, name in items
        ]

        checklist_sections.append(
            '<section>'
            '<h2>{}</h2>'
            '<table class="checklist">{}</table>'
            '</section>'.format(
                escaped(section_title),
                "".join(rows)
            )
        )

    # ==========================================================
    # INSPECTION MEASUREMENTS AND NOTES
    # ==========================================================

    text_rows = "".join(
        "<tr><th>{}</th><td>{}</td></tr>".format(
            escaped(_VEHICLE_INSPECTION_PDF_FIELD_LABELS[name]),
            escaped(textboxes.get(name)),
        )
        for name in _VEHICLE_INSPECTION_TEXTBOXES
    )

    # ==========================================================
    # INSPECTION DATES AND TIMES
    # ==========================================================

    date_rows = "".join(
        "<tr><th>{}</th><td>{}</td></tr>".format(
            escaped(_VEHICLE_INSPECTION_PDF_FIELD_LABELS[name]),
            escaped(dates.get(name)),
        )
        for name in _VEHICLE_INSPECTION_DATES
    )

    # ==========================================================
    # INSPECTION PHOTOS
    # ==========================================================

    photo_labels = {
        "image_1": "Car on jack stands",
        "image_2": "Fault or old part",
        "image_3": "Dashboard with no warning lights",
    }

    photo_cards = []

    for image_code in _VEHICLE_INSPECTION_IMAGES:

        photo_label = photo_labels[image_code]

        media = images.get(image_code)

        image_html = '<p class="missing">No photo saved</p>'

        if media is not None:

            content_type = getattr(media, "content_type", None)

            get_bytes = getattr(media, "get_bytes", None)

            if (
                content_type not in _VEHICLE_INSPECTION_IMAGE_TYPES
                or not callable(get_bytes)
            ):
                raise ValueError(
                    "A saved inspection photo has an unsupported format."
                )

            image_bytes = get_bytes()

            if (
                not isinstance(image_bytes, (bytes, bytearray))
                or not image_bytes
                or len(image_bytes) > _MAX_VEHICLE_INSPECTION_IMAGE_BYTES
            ):
                raise ValueError(
                    "A saved inspection photo is invalid or oversized."
                )

            image_data = base64.b64encode(
                bytes(image_bytes)
            ).decode("ascii")

            image_html = (
                '<img src="data:{};base64,{}" alt="{}">'
            ).format(
                html_module.escape(content_type, quote=True),
                image_data,
                html_module.escape(photo_label, quote=True),
            )

        photo_cards.append(
            '<div class="photo-card">'
            '<h3>{}</h3>{}'
            '</div>'.format(
                escaped(photo_label),
                image_html
            )
        )

    # ==========================================================
    # CALCULATE TOTAL INSPECTION HOURS
    # ==========================================================

    hours = "&mdash;"

    start_time = dates.get("date_picker_time_start")
    end_time = dates.get("date_picker_time_end")

    if start_time and end_time:

        try:

            elapsed = (
                datetime.datetime.fromisoformat(str(end_time))
                - datetime.datetime.fromisoformat(str(start_time))
            ).total_seconds()

            if elapsed >= 0:
                hours = "{:.2f} hours".format(elapsed / 3600)

        except (TypeError, ValueError):

            logging.warning(
                "Invalid inspection time data for job card %s",
                jobCardID
            )

    # ==========================================================
    # GENERATE COMPLETE HTML DOCUMENT
    # ==========================================================

    return f"""<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Vehicle Inspection Checklist</title>

    <style>

        /* ==============================================
        MOZILLA HEADLINE FONT
        ============================================== */

        {font_face}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Mozilla Headline', 'Roboto', 'Noto', Arial, sans-serif;
            font-size: 14px;
            line-height: 1.4286;
            background-color: #fafafa;
            color: rgba(0,0,0,0.87);
            margin: 0;
            padding: 16px;
        }}

        /* ==============================================
        DOCUMENT CONTAINER
        ============================================== */

        .document-container {{
            background-color: white;
            border-radius: 2px;
            box-shadow: 0 2px 2px 0 rgba(0,0,0,0.14),
                        0 3px 1px -2px rgba(0,0,0,0.2),
                        0 1px 5px 0 rgba(0,0,0,0.12);
            max-width: 800px;
            margin: 0 auto;
            overflow: hidden;
        }}

        /* ==============================================
        COMPANY LOGO
        Same dimensions as Technician Notes
        (-webkit-box fallbacks for wkhtmltopdf's old WebKit)
        ============================================== */

        .logo-section {{
            text-align: center;
            padding: 24px;
            background-color: white;
            border-bottom: 1px solid #e0e0e0;
        }}

        .logo-container {{
            display: -webkit-box;
            display: flex;
            -webkit-box-align: center;
            align-items: center;
            -webkit-box-pack: center;
            justify-content: center;
            margin-bottom: 16px;
        }}

        .logo-image {{
            width: 725px;
            height: 100px;
            max-width: 100%;
            background: linear-gradient(
                135deg,
                #228B22,
                #90EE90,
                #FFD700,
                #FF6347
            );
            border-radius: 2px;
            display: -webkit-box;
            display: flex;
            -webkit-box-align: center;
            align-items: center;
            -webkit-box-pack: center;
            justify-content: center;
            font-size: 24px;
            color: white;
            font-weight: 500;
            box-shadow: 0 2px 2px 0 rgba(0,0,0,0.14),
                        0 3px 1px -2px rgba(0,0,0,0.2),
                        0 1px 5px 0 rgba(0,0,0,0.12);
        }}

        .logo-image img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            border-radius: 2px;
        }}

        /* ==============================================
        DOCUMENT HEADER
        ============================================== */

        .header {{
            background-color: #000;
            color: white;
            text-align: center;
            padding: 16px 24px;
            font-size: 16px;
            font-weight: 300;
            letter-spacing: .5px;
            box-shadow: 0 4px 5px 0 rgba(0,0,0,0.14),
                        0 1px 10px 0 rgba(0,0,0,0.12),
                        0 2px 4px -1px rgba(0,0,0,0.2);
        }}

        /* ==============================================
        JOB CARD DETAILS
        ============================================== */

        .job-details {{
            width: 100%;
            table-layout: fixed;
            border-collapse: collapse;
            margin: 24px 0;
            background-color: white;
        }}

        .job-details th,
        .job-details td {{
            border: 1px solid #e0e0e0;
            padding: 8px;
            text-align: left;
            vertical-align: top;
            font-size: 14px;
            overflow-wrap: anywhere;
        }}

        .job-details th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}

        /* ==============================================
        SECTION HEADINGS
        ============================================== */

        h2 {{
            background-color: #f5f5f5;
            border-bottom: 1px solid #e0e0e0;
            padding: 10px;
            font-size: 16px;
            font-weight: bold;
            color: rgba(0,0,0,0.87);
            page-break-after: avoid;
        }}

        h3 {{
            font-size: 14px;
            margin: 0 0 6px;
        }}

        /* ==============================================
        CHECKLIST AND DATA TABLES
        ============================================== */

        .checklist,
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
            background-color: white;
        }}

        .checklist th,
        .checklist td,
        .data-table th,
        .data-table td {{
            border: 1px solid rgba(0,0,0,0.12);
            padding: 10px;
            text-align: left;
            vertical-align: top;
            font-size: 14px;
        }}

        .data-table th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}

        /* Checkbox cell: SVG box/tick, no font glyph needed */
        .checklist td.check {{
            width: 35px;
            text-align: center !important;
            vertical-align: middle;
        }}

        .check svg {{
            display: block;
            margin: 0 auto;
        }}

        section {{
            page-break-inside: auto;
            break-inside: auto;
        }}

        .checklist tr {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        /* ==============================================
        INSPECTION PHOTOS
        ============================================== */

        .photos {{
            page-break-before: always;
        }}

        .photo-card {{
            display: inline-block;
            width: 48%;
            vertical-align: top;
            page-break-inside: avoid;
            margin: 0 1% 14px 0;
        }}

        .photo-card img {{
            width: 100%;
            max-height: 360px;
            object-fit: contain;
        }}

        .missing {{
            border: 1px dashed #9ca3af;
            padding: 30px;
            text-align: center;
            color: #6b7280;
        }}

        /* ==============================================
        TOTAL HOURS
        ============================================== */

        .hours {{
            font-weight: bold;
        }}

        /* ==============================================
        PRINT STYLING
        ============================================== */

        @media print {{

            body {{
                padding: 0;
                background-color: white;
            }}

            .document-container {{
                max-width: 100%;
                box-shadow: none;
            }}

            .logo-image {{
                max-width: 100%;
            }}

        }}

    </style>

</head>

<body>

    <div class="document-container">

        <!-- COMPANY LOGO -->

        <div class="logo-section">

            <div class="logo-container">

                <div class="logo-image">

                    {logo_html}

                </div>

            </div>

        </div>

        <!-- DOCUMENT TITLE -->

        <div class="header">
            VEHICLE INSPECTION CHECKLIST
        </div>

        <!-- JOB CARD DETAILS -->

        <table class="job-details">

            <tr>
                <th>Job Card</th>
                <td>{escaped(jobcard.get('JobCardRef'))}</td>

                <th>Inspection Date</th>
                <td>{escaped(jobcard.get('ReceivedDate'))}</td>
            </tr>

            <tr>
                <th>Customer</th>
                <td>{escaped(jobcard.get('ClientName'))}</td>

                <th>Registration</th>
                <td>{escaped(jobcard.get('RegNo'))}</td>
            </tr>

            <tr>
                <th>Vehicle</th>
                <td>{escaped(jobcard.get('MakeAndModel'))}</td>

                <th>Engine</th>
                <td>{escaped(jobcard.get('EngineCode'))}</td>
            </tr>

            <tr>
                <th>Chassis</th>
                <td>{escaped(jobcard.get('ChassisNo'))}</td>

                <th>Engine Number</th>
                <td>{escaped(jobcard.get('EngineNo'))}</td>
            </tr>

            <tr>
                <th>Mileage</th>
                <td>{escaped(jobcard.get('Mileage'))}</td>

                <th>Total Hours</th>
                <td class="hours">{hours}</td>
            </tr>

        </table>

        <!-- INSPECTION CHECKLIST -->

        <h2>Inspection Checklist</h2>

        {''.join(checklist_sections)}

        <!-- INSPECTION MEASUREMENTS AND NOTES -->

        <h2>Inspection Measurements and Notes</h2>

        <table class="data-table">

            {text_rows}

        </table>

        <!-- INSPECTION DATES AND TIMES -->

        <h2>Dates and Times</h2>

        <table class="data-table">

            {date_rows}

        </table>

        <!-- INSPECTION PHOTOS -->

        <div class="photos">

            <h2>Inspection Photos</h2>

            {''.join(photo_cards)}

        </div>

        <!-- FOOTER -->

        <footer id="footer">

            <div style="
                width:80%;
                margin:24px auto;
                text-align:center;
                font-size:12px;
                font-family:'Mozilla Headline',Arial,sans-serif;
            ">

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
@anvil.server.callable()
def downloadInspectionChecklistPdf(jobCardID, docType):
    _get_current_user()
    if type(jobCardID) is not int or jobCardID <= 0:
        raise ValueError("Invalid job card ID.")
    if docType != "InspectionChecklist":
        raise ValueError("Unsupported inspection checklist document type.")

    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix="inspection-checklist-", suffix=".pdf"
    )
    os.close(file_descriptor)
    try:
        html_string = fillInspectionChecklistData(jobCardID, docType)
        pdfkit.from_string(
            html_string,
            temporary_path,
            options={
                "encoding": "UTF-8",
                "page-size": "A4",
                "orientation": "Portrait",
                "margin-top": "0.75in",
                "margin-right": "0.75in",
                "margin-bottom": "0.75in",
                "margin-left": "0.75in",
                "no-outline": False,
                "enable-local-file-access": None,
                "quiet": "",
            },
            configuration=config,
        )
        return anvil.media.from_file(
            temporary_path,
            "application/pdf",
            name="InspectionChecklist-{}.pdf".format(jobCardID),
        )
    except Exception:
        logging.exception(
            "Inspection checklist PDF generation failed for job card %s", jobCardID
        )
        raise
    finally:
        try:
            os.remove(temporary_path)
        except FileNotFoundError:
            pass
        except OSError:
            logging.exception("Could not remove a temporary inspection checklist PDF.")

__all__ = [
    '_VEHICLE_INSPECTION_SECTIONS',
    '_VEHICLE_INSPECTION_CHECKBOXES',
    '_VEHICLE_INSPECTION_TEXTBOXES',
    '_VEHICLE_INSPECTION_DATES',
    '_VEHICLE_INSPECTION_PDF_FIELD_LABELS',
    '_VEHICLE_INSPECTION_IMAGES',
    '_VEHICLE_INSPECTION_ITEM_CODE_PREFIX',
    '_SELF_SERVICE_INSPECTION_CHECKBOX_COMPONENTS',
    '_SELF_SERVICE_INSPECTION_FIELD_COMPONENTS',
    '_SELF_SERVICE_INSPECTION_SECTION_ITEMS',
    '_SELF_SERVICE_INSPECTION_SECTION_CHECKBOXES',
    '_VEHICLE_INSPECTION_IMAGE_TYPES',
    '_MAX_VEHICLE_INSPECTION_IMAGE_BYTES',
    '_validate_vehicle_inspection_data',
    '_prepare_vehicle_inspection_images',
    '_is_vehicle_inspection_image_path',
    '_write_vehicle_inspection_images',
    '_upsert_vehicle_inspection_image_rows',
    '_persist_vehicle_inspection_images',
    '_remove_vehicle_inspection_images',
    'save_update_vehicle_inspection',
    'get_vehicle_inspection_data',
    'get_inspection_checklist_data_by_job_id',
    '_get_inspection_checklist_data',
    'fillInspectionChecklistData',
    'downloadInspectionChecklistPdf',
]

from . import BMALocal as _compatibility_facade
