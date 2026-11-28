from ._common import *

# ***************************************************FAQ Section ************************************


@anvil.server.callable()
def get_faq_html():
    _get_current_user()
    with db_cursor() as cursor:
        # Fetch questions and answers from table
        cursor.execute("SELECT Question, Answer FROM tbl_faqs ORDER BY id ASC")
        faqs = cursor.fetchall()

        # HTML Template start
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>FAQs</title>
            <style>
                /* --- Embed Mozilla Headline font --- */
                @font-face {{
                    font-family: 'Mozilla Headline';
                    src: url(data:font/ttf;base64,{font_base64}) format('truetype');
                }}
                .faq-container {
                    max-width: 800px;
                    margin: auto;
                    padding: 20px;
                    font-family: Arial, sans-serif;
                }
                .faq-container h2 {
                    text-align: center;
                    margin-bottom: 20px;
                    font-family: 'Mozilla Headline';
                    color: white;
                }
                .faq-item {
                    border-bottom: 1px solid #ccc;
                }
                .faq-question {
                    background-color: #f9f9f9;
                    color: #333;
                    padding: 15px;
                    width: 100%;
                    text-align: left;
                    border: none;
                    outline: none;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                    font-family: 'Mozilla Headline';
                }
                .faq-question:hover {
                    background-color: #eee;
                }
                .faq-answer {
                    display: none;
                    padding: 15px;
                    background-color: #fff;
                    color: #555;
                    font-family: 'Mozilla Headline';
                }
                .faq-answer p {
                    margin: 0;
                }
            </style>
        </head>
        <body>
            <div class="faq-container">
                <h2>Frequently Asked Questions</h2>
        """

        # Add FAQ items dynamically — escape DB content to prevent XSS
        for row in faqs:
            question = html_module.escape(str(row[0]))
            answer = html_module.escape(str(row[1]))
            html += f"""
            <div class="faq-item">
                <button class="faq-question">{question}</button>
                <div class="faq-answer">
                    <p>{answer}</p>
                </div>
            </div>
            """

        # Close HTML and add JavaScript
        html += """
            </div>
                <script>
                        (function(){
                            const questions = document.querySelectorAll(".faq-question");
                            questions.forEach((question) => {
                                question.addEventListener("click", function () {
                                    const answer = this.nextElementSibling;
                                    document.querySelectorAll(".faq-answer").forEach((a) => {
                                        if (a !== answer) a.style.display = "none";
                                    });
                                    answer.style.display =
                                        answer.style.display === "block" ? "none" : "block";
                                });
                            });
                        })();
                </script>
        </body>
        </html>
        """

        return html


# ***************************************************Client Section ************************************


# Get client's name to be displayed in job card
@anvil.server.callable()
def getClientFullname():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, Fullname, Phone, Address, Email, Narration FROM tbl_clientcontacts
            ORDER BY Fullname ASC  
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        result = [
            {
                "ID": row[0],
                "Fullname": row[1],
                "Phone": row[2],
                "Address": row[3],
                "Email": row[4],
                "Narration": row[5],
            }
            for row in rows
        ]
    return result



@anvil.server.callable()
def getClientFullnameFromSearchWord(valueSearch):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, Fullname FROM tbl_clientcontacts
            WHERE Fullname LIKE %s or Phone Like %s
            ORDER BY Fullname ASC  
        """
        like_pattern = f"%{valueSearch}%"
        cursor.execute(query, (like_pattern, like_pattern))
        rows = cursor.fetchall()
        return [(row[1], row[0]) for row in rows]  # (RegNo, ID)


# Get client details with ID
@anvil.server.callable()
def getClientNameWithID(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, Fullname, Phone, Address, Email, Narration FROM tbl_clientcontacts
            WHERE ID = %s 
        """
        cursor.execute(query, (valueID,))
        rows = cursor.fetchall()
        result = [
            {
                "ID": row[0],
                "Fullname": row[1],
                "Phone": row[2],
                "Address": row[3],
                "Email": row[4],
                "Narration": row[5],
            }
            for row in rows
        ]

    return result[0]


# Save new client data
@anvil.server.callable()
def save_client_data(name, phone, address, email, narration):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_clientcontacts (Fullname, Phone, Address, Email, Narration)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, phone, address, email, narration))
        new_id = cursor.lastrowid
    publish_realtime_event("contacts", "client_created", entity_id=new_id)


# Get Client report
@anvil.server.callable()
def getClientReport(clientID):
    _get_current_user()
    with db_cursor() as cursor:
        if clientID is None:
            query = (
                "SELECT ID , Fullname, Phone, Address, Email, Narration "
                "FROM tbl_clientcontacts "
                "ORDER BY Fullname ASC"
            )
            cursor.execute(query)
        else:
            query = (
                "SELECT ID , Fullname, Phone, Address, Email, Narration "
                "FROM tbl_clientcontacts "
                "WHERE ID = %s"
            )
            cursor.execute(query, (clientID,))

        rows = cursor.fetchall()
        result = [
            {
                "No": index + 1,
                "ID": row[0],
                "Fullname": row[1],
                "Phone": row[2],
                "Address": row[3],
                "Email": row[4],
                "Narration": row[5],
            }
            for index, row in enumerate(rows)
        ]

    return result


@anvil.server.callable()
def get_client_report_paginated(clientID=None, limit=50, offset=0):
    """Paginated client report using MySQL COUNT(*) + LIMIT/OFFSET."""
    _get_current_user()
    if not isinstance(limit, int) or limit <= 0 or limit > 200:
        raise ValueError("limit must be an integer between 1 and 200.")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer.")

    with db_cursor() as cursor:
        if clientID is None:
            cursor.execute("SELECT COUNT(*) FROM tbl_clientcontacts")
            total = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT ID, Fullname, Phone, Address, Email, Narration
                FROM tbl_clientcontacts
                ORDER BY Fullname ASC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM tbl_clientcontacts WHERE ID = %s",
                (clientID,),
            )
            total = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT ID, Fullname, Phone, Address, Email, Narration
                FROM tbl_clientcontacts
                WHERE ID = %s
                LIMIT %s OFFSET %s
                """,
                (clientID, limit, offset),
            )

        rows = cursor.fetchall()
        items = [
            {
                "No": offset + index + 1,
                "ID": row[0],
                "Fullname": row[1],
                "Phone": row[2],
                "Address": row[3],
                "Email": row[4],
                "Narration": row[5],
            }
            for index, row in enumerate(rows)
        ]

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@anvil.server.callable()
def updateClientDetails(client_id, name, phone, address, email, narration):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_clientcontacts
            SET Fullname = %s,
                Phone = %s,
                Address = %s,
                Email = %s,
                Narration = %s
            WHERE ID = %s
        """
        cursor.execute(query, (name, phone, address, email, narration, client_id))
    publish_realtime_event("contacts", "client_updated", entity_id=client_id)


@anvil.server.callable()
def getClientNameAndPhoneNumber(value):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
        SELECT ID, Fullname, Phone 
        FROM tbl_clientcontacts 
        WHERE Fullname LIKE %s OR Phone LIKE %s
        ORDER BY Fullname ASC
        """
        like_value = f"%{value}%"
        cursor.execute(query, (like_value, like_value))
        result = cursor.fetchall()
        # Return tuples: (Label shown, Value stored)
        return [(f"{r[1]} - {r[2]}", r[0]) for r in result]


# ***************************************************Technicians Details Section ************************************


@anvil.server.callable()
def getTechnicianReport(technicianName):
    _get_current_user()
    with db_cursor() as cursor:
        if technicianName is None:
            query = """
                SELECT tbl_technicians.ID, tbl_technicians.Fullname, tbl_technicians.Phone, tbl_toolkits.ToolkitName, tbl_technicians.IsArchived 
                FROM tbl_technicians 
                INNER JOIN 
                tbl_toolkits ON tbl_technicians.ToolkitID = tbl_toolkits.ID 
                 ORDER BY Fullname ASC
                """

            cursor.execute(query)
        else:
            query = """
                SELECT tbl_technicians.ID, tbl_technicians.Fullname, tbl_technicians.Phone, tbl_toolkits.ToolkitName,tbl_technicians.IsArchived 
                FROM tbl_technicians 
                INNER JOIN 
                tbl_toolkits ON tbl_technicians.ToolkitID = tbl_toolkits.ID 
                WHERE tbl_technicians.Fullname Like %s
                """
            cursor.execute(query, (f"%{technicianName}%",))
        # Fetch all rows
        rows = cursor.fetchall()
        result = [
            {
                "No": index + 1,
                "ID": row[0],
                "Fullname": row[1],
                "Phone": row[2],
                "Toolkit": row[3],
                "IsArchived": "Yes" if row[4] == 1 else "No",
            }
            for index, row in enumerate(rows)
        ]

    return result



@anvil.server.callable()
def getTechnicians():
    _get_current_user()
    def _load():
        with db_cursor() as cursor:
            query = """
                SELECT ID, Fullname
                FROM tbl_technicians
                WHERE IsArchived = FALSE
                ORDER BY Fullname ASC
            """
            cursor.execute(query)
            result = cursor.fetchall()
            return [{"ID": r[0], "Fullname": r[1]} for r in result]
    return list(cached_lookup("technicians", _load, ttl_seconds=300))


@anvil.server.callable()
def getAssignedTechnician(id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT tbl_technicians.Fullname 
            FROM tbl_pendingassignedjobs 
            INNER JOIN 
            tbl_technicians ON tbl_pendingassignedjobs.TechnicianID = tbl_technicians.ID 
            WHERE tbl_pendingassignedjobs.JobCardRefID = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        if result is None:
            return None
        else:
            return result[0]


@anvil.server.callable()
def save_technician_data(fullname, phone, toolkit):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_technicians(Fullname,Phone,ToolkitID,IsArchived) VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (fullname, phone, toolkit, 0))
        new_id = cursor.lastrowid
    invalidate_lookup_cache("technicians", "staff_and_technician_names")
    publish_realtime_event("contacts", "technician_created", entity_id=new_id)


@anvil.server.callable()
def get_technician_details(value):
    _get_current_user()
    with db_cursor() as cursor:
        if value is None:
            query = """
                SELECT ID, Fullname, Phone, ToolkitID, IsArchived 
                FROM tbl_technicians 
                ORDER BY Fullname ASC
            """
            cursor.execute(query)
        else:
            query2 = """
                            SELECT ID, Fullname, Phone, ToolkitID, IsArchived 
                            FROM tbl_technicians 
                            WHERE ID = %s
                        """
            cursor.execute(query2, (value,))

        rows = cursor.fetchall()
        result = [
            {
                "ID": row[0],
                "Fullname": row[1],
                "Phone": row[2],
                "ToolkitID": row[3],
                "Active": "Yes" if row[4] == 1 else "No",
            }
            for row in rows
        ]

        return result



@anvil.server.callable()
def update_technician_data(name, phone, toolkit, archived, technician_id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_technicians
            SET Fullname = %s,
                Phone = %s,
                ToolkitID = %s,
                IsArchived = %s
            WHERE ID = %s
        """
        cursor.execute(query, (name, phone, toolkit, archived, technician_id))
    invalidate_lookup_cache("technicians", "staff_and_technician_names")
    publish_realtime_event("contacts", "technician_updated", entity_id=technician_id)


@anvil.server.callable()
def getTechnicianDetailsFromName(valueName):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, Fullname
            FROM tbl_technicians
            WHERE IsArchived = FALSE AND Fullname = %s
            ORDER BY Fullname ASC
        """
        cursor.execute(query, (valueName,))
        result = cursor.fetchall()
        return [{"ID": r[0], "Fullname": r[1]} for r in result]


@anvil.server.callable()
def getTechnicianNameAndID(valueName):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, Fullname
            FROM tbl_technicians
            WHERE Fullname LIKE %s
            ORDER BY Fullname ASC
        """
        cursor.execute(query, (f"%{valueName}%",))
        result = cursor.fetchall()
        return [(f"{r[1]}", r[0]) for r in result]


@anvil.server.callable()
def getTechnicianInJobCard():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT ID, Fullname
            FROM tbl_technicians
            WHERE IsArchived = FALSE
            ORDER BY Fullname ASC
        """
        cursor.execute(query)
        result = cursor.fetchall()
        return [(r[1], r[0]) for r in result]


# ***************************************************Toolkit Section ************************************


@anvil.server.callable()
def get_toolkits(value=None):
    _get_current_user()
    if value is None:
        def _load_toolkits():
            with db_cursor() as cursor:
                cursor.execute(
                    "SELECT ID, ToolkitName, Cost FROM tbl_toolkits ORDER BY ToolkitName ASC"
                )
                rows = cursor.fetchall()
                return [
                    {
                        "ID": row[0],
                        "ToolkitName": row[1],
                        "Cost": row[2] if len(row) > 2 else None,
                    }
                    for row in rows
                ]
        return list(cached_lookup("toolkits", _load_toolkits, ttl_seconds=300))

    with db_cursor() as cursor:
        cursor.execute(
            "SELECT ID, ToolkitName, Cost FROM tbl_toolkits WHERE ID = %s",
            (value,),
        )
        rows = cursor.fetchall()
        return [
            {
                "ID": row[0],
                "ToolkitName": row[1],
                "Cost": row[2] if len(row) > 2 else None,
            }
            for row in rows
        ]


# Check for existing toolkits
@anvil.server.callable()
def check_duplicate_toolkit(value):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT ID 
                FROM tbl_toolkits 
                WHERE ToolkitName = %s
            """
        cursor.execute(query, (value,))

        result = cursor.fetchone()
        return result is not None


@anvil.server.callable()
def save_toolkit_data(name, amount):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                INSERT INTO tbl_toolkits(ToolkitName, Cost) 
                VALUES(%s, %s)
        """
        cursor.execute(query, (name, amount))
        new_id = cursor.lastrowid
    invalidate_lookup_cache("toolkits")
    publish_realtime_event("contacts", "toolkit_created", entity_id=new_id)


@anvil.server.callable()
def get_toolkit_details(value):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                            SELECT ID, ToolkitName, Cost
                            FROM tbl_toolkits 
                            WHERE ID = %s
                        """
        cursor.execute(query, (value,))

        rows = cursor.fetchall()
        result = [{"ID": row[0], "ToolkitName": row[1], "Cost": row[2]} for row in rows]

        return result



@anvil.server.callable()
def update_toolkit_data(name, amount, toolkit_id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_toolkits
            SET ToolkitName = %s,
                Cost = %s
            WHERE ID = %s
        """
        cursor.execute(query, (name, amount, toolkit_id))
    invalidate_lookup_cache("toolkits")
    publish_realtime_event("contacts", "toolkit_updated", entity_id=toolkit_id)


# ***************************************************Staff Details Section ************************************


@anvil.server.callable()
def save_staff_data(fullname, phone):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_checkstaff(Staff,Phone,IsArchived) VALUES (%s, %s, %s)
        """
        cursor.execute(query, (fullname, phone, 0))
        new_id = cursor.lastrowid
    invalidate_lookup_cache("staff", "staff_and_technician_names")
    publish_realtime_event("contacts", "staff_created", entity_id=new_id)


@anvil.server.callable()
def get_staff_details(value):
    _get_current_user()
    with db_cursor() as cursor:
        if value is None:
            query = """
                SELECT ID, Staff, Phone, IsArchived 
                FROM tbl_checkstaff 
                ORDER BY Staff ASC
            """
            cursor.execute(query)
        else:
            query2 = """
                            SELECT ID, Staff, Phone, IsArchived
                            FROM tbl_checkstaff 
                            WHERE ID = %s
                        """
            cursor.execute(query2, (value,))

        rows = cursor.fetchall()
        result = [
            {
                "ID": row[0],
                "Fullname": row[1],
                "Phone": row[2],
                "Active": "Yes" if row[3] == 1 else "No",
            }
            for row in rows
        ]

        return result



@anvil.server.callable()
def update_staff_data(name, phone, archived, staff_id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_checkstaff
            SET Staff = %s,
                Phone = %s,
                IsArchived = %s
            WHERE ID = %s
        """
        cursor.execute(query, (name, phone, archived, staff_id))
    invalidate_lookup_cache("staff", "staff_and_technician_names")
    publish_realtime_event("contacts", "staff_updated", entity_id=staff_id)


@anvil.server.callable()
def getStaffReport(staffID):
    _get_current_user()
    with db_cursor() as cursor:
        if staffID is None:
            query = (
                "SELECT ID, Staff, Phone, IsArchived"
                " FROM tbl_checkstaff "
                " ORDER BY Staff ASC"
            )
            cursor.execute(query)
        else:
            query = (
                "SELECT ID, Staff, Phone, IsArchived "
                "FROM tbl_checkstaff "
                "WHERE ID = %s"
            )
            cursor.execute(query, (staffID,))

        rows = cursor.fetchall()
        result = [
            {
                "No": index + 1,
                "ID": row[0],
                "Fullname": row[1],
                "Phone": row[2],
                "Active": "Yes" if row[3] == 1 else "No",
            }
            for index, row in enumerate(rows)
        ]

    return result



# Get Staff Details
@anvil.server.callable()
def getStaff():
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
            return [{"ID": r[0], "Staff": r[1]} for r in result]
    return list(cached_lookup("staff", _load, ttl_seconds=300))


@anvil.server.callable()
def getStaffByName(valueName):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT ID, Staff
                FROM tbl_checkstaff
                WHERE Staff LIKE %s
                 ORDER BY Staff ASC
            """
        cursor.execute(query, (f"%{valueName}%",))
        result = cursor.fetchall()
        return [(f"{r[1]}", r[0]) for r in result]


# Get Staff Details By ID
@anvil.server.callable()
def getStaffByID(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT ID, Staff
                FROM tbl_checkstaff
                WHERE ID = %s
                ORDER BY Staff ASC
            """
        cursor.execute(query, (valueID,))
        result = cursor.fetchall()
        return [{"ID": r[0], "Staff": r[1]} for r in result]


@anvil.server.callable()
def getStaffAndTechnicianNames():
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
        result = cursor.fetchall()
        
        # Modern list comprehension that handles both DictCursor and TupleCursor
        names = []
        for r in result:
            # If r is a dict, get 'combined_name'. If it's a tuple/list, get index 0.
            val = r['combined_name'] if isinstance(r, dict) else r[0]
            names.append((val, val))
            
        return names
    
# ***************************************************Duplicate Phone Number Details Section ************************************


# Check for existing contacts
@anvil.server.callable()
def check_duplicate_contact(contacttype, phone):
    _get_current_user()
    with db_cursor() as cursor:
        if contacttype == "Client":
            query = """
                SELECT ID FROM tbl_clientcontacts 
                WHERE Phone = %s
            """
            cursor.execute(query, (phone,))
        elif contacttype == "Technician":
            query2 = """
                            SELECT ID FROM tbl_technicians 
                            WHERE Phone = %s
                        """
            cursor.execute(query2, (phone,))
        elif contacttype == "Staff":
            query3 = """
                            SELECT ID FROM tbl_checkstaff 
                            WHERE Phone = %s
                        """
            cursor.execute(query3, (phone,))
        elif contacttype == "Supplier":
            query4 = """
                            SELECT ID FROM tbl_carpartssupplier 
                            WHERE Phone = %s
                        """
            cursor.execute(query4, (phone,))
        result = cursor.fetchone()
        return result is not None

__all__ = [
    'get_faq_html',
    'getClientFullname',
    'getClientFullnameFromSearchWord',
    'getClientNameWithID',
    'save_client_data',
    'getClientReport',
    'get_client_report_paginated',
    'updateClientDetails',
    'getClientNameAndPhoneNumber',
    'getTechnicianReport',
    'getTechnicians',
    'getAssignedTechnician',
    'save_technician_data',
    'get_technician_details',
    'update_technician_data',
    'getTechnicianDetailsFromName',
    'getTechnicianNameAndID',
    'getTechnicianInJobCard',
    'get_toolkits',
    'check_duplicate_toolkit',
    'save_toolkit_data',
    'get_toolkit_details',
    'update_toolkit_data',
    'save_staff_data',
    'get_staff_details',
    'update_staff_data',
    'getStaffReport',
    'getStaff',
    'getStaffByName',
    'getStaffByID',
    'getStaffAndTechnicianNames',
    'check_duplicate_contact',
]

from . import BMALocal as _compatibility_facade
