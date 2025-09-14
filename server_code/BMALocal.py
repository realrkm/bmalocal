import anvil.server
import mysql.connector
from dotenv import load_dotenv
import os
from contextlib import contextmanager
import re
import anvil.media
import pdfkit
import decimal
import base64
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from io import BytesIO
import datetime
from anvil.tables import app_tables
import anvil.users


# Set your wkhtmltopdf path here (adjust for your system)
WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"  # Windows path
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

# Load environment variables from .env file
load_dotenv()


# Function to establish DB connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "3306"),
        database=os.getenv("DB_NAME"),
        auth_plugin=os.getenv("DB_AUTH_PLUGIN", "mysql_native_password")
    )


# Context manager for DB cursor
@contextmanager
def db_cursor():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


# ***************************************************FAQ Section ************************************

@anvil.server.callable
def get_faq_html():
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
            <link href="https://fonts.googleapis.com/css2?family=Mozilla+Headline&display=swap" rel="stylesheet">
            <style>
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

        # Add FAQ items dynamically
        for row in faqs:
            html += f"""
            <div class="faq-item">
                <button class="faq-question">{row[0]}</button>
                <div class="faq-answer">
                    <p>{row[1]}</p>
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
                "Narration": row[5]
            }
            for row in rows
        ]
    return result


# Get client details with ID
@anvil.server.callable()
def getClientNameWithID(valueID):
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
                "Narration": row[5]
            }
            for row in rows
        ]

    return result[0]


# Save new client data
@anvil.server.callable()
def save_client_data(name, phone, address, email, narration):
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_clientcontacts (Fullname, Phone, Address, Email, Narration)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, phone, address, email, narration))


# Get Client report
@anvil.server.callable()
def getClientReport(clientID):
    with db_cursor() as cursor:
        if clientID is None:
            query = ("SELECT ID , Fullname, Phone, Address, Email, Narration "
                     "FROM tbl_clientcontacts "
                     "ORDER BY Fullname ASC")
            cursor.execute(query)
        else:
            query = ("SELECT ID , Fullname, Phone, Address, Email, Narration "
                     "FROM tbl_clientcontacts "
                     "WHERE ID = %s")
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
                "Narration": row[5]
            }
            for index, row in enumerate(rows)
        ]

    return result


@anvil.server.callable()
def updateClientDetails(client_id, name, phone, address, email, narration):
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


@anvil.server.callable()
def getClientNameAndPhoneNumber(value):
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
                "IsArchived": "Yes" if row[4] == 1 else "No"
            }
            for index, row in enumerate(rows)
        ]

    return result


@anvil.server.callable()
def getTechnicians():
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


@anvil.server.callable()
def getAssignedTechnician(id):
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
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_technicians(Fullname,Phone,ToolkitID,IsArchived) VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (fullname, phone, toolkit, 0))


@anvil.server.callable()
def get_technician_details(value):
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
                "Active": "Yes" if row[4] == 1 else "No"
            }
            for row in rows
        ]

        return result


@anvil.server.callable()
def update_technician_data(name, phone, toolkit, archived, technician_id):
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

@anvil.server.callable()
def getTechnicianDetailsFromName(valueName):
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
def getTechnicianInJobCard():
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
def get_toolkits(value):
    with db_cursor() as cursor:
        if value is None:
            query = """
                SELECT ID, ToolkitName FROM tbl_toolkits ORDER BY ToolkitName ASC
            """
            cursor.execute(query)
        else:
            query2 = """
                        SELECT ID, ToolkitName FROM tbl_toolkits WHERE ID = %s
                    """
            cursor.execute(query2, (value,))

        result = cursor.fetchall()

        return [{"ID": row[0], "ToolkitName": row[1]} for row in result]


# Check for existing toolkits
@anvil.server.callable()
def check_duplicate_toolkit(value):
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
    with db_cursor() as cursor:
        query = """
                INSERT INTO tbl_toolkits(ToolkitName, Cost) 
                VALUES(%s, %s)
        """
        cursor.execute(query, (name, amount))


@anvil.server.callable()
def get_toolkit_details(value):
    with db_cursor() as cursor:
        query = """
                            SELECT ID, ToolkitName, Cost
                            FROM tbl_toolkits 
                            WHERE ID = %s
                        """
        cursor.execute(query, (value,))

        rows = cursor.fetchall()
        result = [
            {
                "ID": row[0],
                "ToolkitName": row[1],
                "Cost": row[2]
            }
            for row in rows
        ]

        return result


@anvil.server.callable()
def update_toolkit_data(name, amount, toolkit_id):
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_toolkits
            SET ToolkitName = %s,
                Cost = %s
            WHERE ID = %s
        """
        cursor.execute(query, (name, amount, toolkit_id))


# ***************************************************Staff Details Section ************************************

@anvil.server.callable()
def save_staff_data(fullname, phone):
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_checkstaff(Staff,Phone,IsArchived) VALUES (%s, %s, %s)
        """
        cursor.execute(query, (fullname, phone, 0))


@anvil.server.callable()
def get_staff_details(value):
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
                "Active": "Yes" if row[3] == 1 else "No"
            }
            for row in rows
        ]

        return result


@anvil.server.callable()
def update_staff_data(name, phone, archived, staff_id):
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_checkstaff
            SET Staff = %s,
                Phone = %s,
                IsArchived = %s
            WHERE ID = %s
        """
        cursor.execute(query, (name, phone, archived, staff_id))


@anvil.server.callable()
def getStaffReport(staffID):
    with db_cursor() as cursor:
        if staffID is None:
            query = ("SELECT ID, Staff, Phone, IsArchived"
                     " FROM tbl_checkstaff "
                     " ORDER BY Staff ASC")
            cursor.execute(query)
        else:
            query = ("SELECT ID, Staff, Phone, IsArchived "
                     "FROM tbl_checkstaff "
                     "WHERE ID = %s")
            cursor.execute(query, (staffID,))

        rows = cursor.fetchall()
        result = [
            {
                "No": index + 1,
                "ID": row[0],
                "Fullname": row[1],
                "Phone": row[2],
                "Active": "Yes" if row[3] == 1 else "No"

            }
            for index, row in enumerate(rows)
        ]

    return result


# Get Staff Details
@anvil.server.callable()
def getStaff():
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


# Get Staff Details By ID
@anvil.server.callable()
def getStaffByID(valueID):
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


# ***************************************************Car Details Section ************************************

@anvil.server.callable()
def getCarRegistration():
    with db_cursor() as cursor:
        query = """
            SELECT MAX(ID) as LastOfID, RegNo
            FROM tbl_jobcarddetails
            GROUP BY RegNo
            ORDER BY RegNo ASC
        """

        cursor.execute(query)
        result = cursor.fetchall()
        return [{"ID": r[0], "RegNo": r[1]} for r in result]


@anvil.server.callable
def get_car_details(search_term):
    with db_cursor() as cursor:
        if search_term is None:
            query = """
                SELECT 
                    tbl_clientcontacts.Fullname, 
                    tbl_clientcontacts.Phone, 
                    tbl_jobcarddetails.RegNo, 
                    tbl_jobcarddetails.ChassisNo,
                    tbl_jobcarddetails.ReceivedDate,
                    tbl_jobcarddetails.JobCardRef
                FROM 
                    tbl_clientcontacts 
                INNER JOIN 
                    tbl_jobcarddetails 
                ON 
                    tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails 
                GROUP BY 
                    tbl_clientcontacts.Fullname, 
                    tbl_clientcontacts.Phone, 
                    tbl_jobcarddetails.RegNo, 
                    tbl_jobcarddetails.ChassisNo,
                    tbl_jobcarddetails.ReceivedDate,
                    tbl_jobcarddetails.JobCardRef
                ORDER BY Max(tbl_jobcarddetails.ReceivedDate) DESC
            """
            cursor.execute(query)
        else:
            query = """
                        SELECT 
                            tbl_clientcontacts.Fullname, 
                            tbl_clientcontacts.Phone, 
                            tbl_jobcarddetails.RegNo, 
                            tbl_jobcarddetails.ChassisNo,
                            tbl_jobcarddetails.ReceivedDate,
                            tbl_jobcarddetails.JobCardRef
                        FROM 
                            tbl_clientcontacts 
                        INNER JOIN 
                            tbl_jobcarddetails 
                        ON 
                            tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails 
                        WHERE 
                            tbl_clientcontacts.Fullname LIKE %s 
                            OR 
                                tbl_clientcontacts.Phone LIKE %s 
                            OR  
                                tbl_jobcarddetails.RegNo LIKE %s 
                            OR  
                                tbl_jobcarddetails.ChassisNo LIKE %s
                        GROUP BY 
                            tbl_clientcontacts.Fullname, 
                            tbl_clientcontacts.Phone, 
                            tbl_jobcarddetails.RegNo, 
                            tbl_jobcarddetails.ChassisNo,
                            tbl_jobcarddetails.ReceivedDate,
                            tbl_jobcarddetails.JobCardRef
                        ORDER BY Max(tbl_jobcarddetails.ReceivedDate) DESC
                            """
            like_pattern = f"%{search_term}%"
            cursor.execute(query, (like_pattern, like_pattern, like_pattern, like_pattern))

        results = cursor.fetchall()

        # Add row numbers using enumerate starting from 1
        return [
            {
                "No": i + 1,
                "Fullname": row[0],
                "Phone": row[1],
                "RegNo": row[2],
                "ChassisNo": row[3],
                "ReceivedDate": row[4],
                "JobCardRef": row[5]
            }
            for i, row in enumerate(results)
        ]

@anvil.server.callable
def get_car_details_and_parts(search_term, part_name):
    with db_cursor() as cursor:
        query = """
                SELECT 
                    tbl_clientcontacts.Fullname, 
                    tbl_clientcontacts.Phone, 
                    tbl_jobcarddetails.RegNo, 
                    tbl_jobcarddetails.ChassisNo,
                    tbl_jobcarddetails.ReceivedDate,
                    tbl_jobcarddetails.JobCardRef
                FROM 
                    tbl_clientcontacts 
                INNER JOIN 
                    tbl_jobcarddetails 
                ON 
                    tbl_clientcontacts.ID = tbl_jobcarddetails.ClientDetails 
                INNER JOIN 
                    tbl_invoices
                ON
                    tbl_invoices.AssignedJobID = tbl_jobcarddetails.ID
                WHERE 
                    (
                        tbl_clientcontacts.Fullname LIKE %s 
                        OR tbl_clientcontacts.Phone LIKE %s 
                        OR tbl_jobcarddetails.RegNo LIKE %s 
                        OR tbl_jobcarddetails.ChassisNo LIKE %s
                    )
                    AND tbl_invoices.Item LIKE %s
                GROUP BY 
                    tbl_clientcontacts.Fullname, 
                    tbl_clientcontacts.Phone, 
                    tbl_jobcarddetails.RegNo, 
                    tbl_jobcarddetails.ChassisNo,
                    tbl_jobcarddetails.ReceivedDate,
                    tbl_jobcarddetails.JobCardRef
                ORDER BY 
                    MAX(tbl_jobcarddetails.ReceivedDate) DESC
            """
        like_pattern = f"%{search_term}%"
        part_pattern = f"%{part_name}%"
        cursor.execute(query, (like_pattern, like_pattern, like_pattern, like_pattern, part_pattern))

        results = cursor.fetchall()

        # Add row numbers using enumerate starting from 1
        return [
            {
                "No": i + 1,
                "Fullname": row[0],
                "Phone": row[1],
                "RegNo": row[2],
                "ChassisNo": row[3],
                "ReceivedDate": row[4],
                "JobCardRef": row[5]
            }
            for i, row in enumerate(results)
        ]

# ***************************************************Job Card Details Section ************************************

@anvil.server.callable()
def getJobCardInstructions(id):
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
            text_only = re.sub(r'<[^>]+>', '', raw_instructions)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""


@anvil.server.callable()
def getJobCardTechNotes(id):
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
            text_only = re.sub(r'<[^>]+>', '', raw_instructions)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""


# Return a specific row from job card table
@anvil.server.callable()
def getJobCardRow(IdValue):
    with db_cursor() as cursor:
        query = """
            SELECT 
                ID, ClientDetails, RegNo, MakeAndModel, ChassisNo,
                EngineCC, EngineNo, EngineCode, Manual, Auto,
                PaintCode, Comp, TPO, JobCardRef,ReceivedDate, DueDate, ExpDate,
                CheckedInBy, Spare, Jack, Brace, Mileage, `Empty`, `Quarter`, Half,
                ThreeQuarter, `Full`, ClientInstruction, Notes, Status  
            FROM tbl_jobcarddetails 
            WHERE ID = %s 
        """
        cursor.execute(query, (IdValue,))
        result = cursor.fetchone()
        if result:
            x = {
                "ID": result[0], "ClientDetails": result[1], "RegNo": result[2],
                "MakeAndModel": result[3], "ChassisNo": result[4], "EngineCC": result[5],
                "EngineNo": result[6], "EngineCode": result[7],
                "Manual": result[8], "Auto": result[9], "PaintCode": result[10], "Comprehensive": result[11],
                "ThirdParty": result[12], "JobCardRef": result[13], "ReceivedDate": result[14], "DueDate": result[15],
                "ExpDate": result[16], "CheckedInBy": result[17], "Spare": result[18], "Jack": result[19],
                "Brace": result[20],
                "Mileage": result[21], "Empty": result[22], "Quarter": result[23], "Half": result[24],
                "ThreeQuarter": result[25],
                "Full": result[26], "ClientInstruction": result[27], "Notes": result[28], "Status": result[29]
            }

            return x
        else:
            return None

@anvil.server.callable()
def getJobCardRowWithClientID(IdValue):
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
                "EngineCode": result[5]
            }
        else:
            return None

# Check for job card ref duplicate
@anvil.server.callable()
def check_job_card_duplicate(JobCardRef):
    with db_cursor() as cursor:
        query = """
            SELECT ID FROM tbl_jobcarddetails 
            WHERE JobCardRef = %s 
        """
        cursor.execute(query, (JobCardRef,))
        result = cursor.fetchone()
        return result is not None


# Save new job card data
@anvil.server.callable()
def save_job_card_details(
        technicianDetails, ClientDetails, JobCardRef, ReceivedDate, DueDate, ExpDate, CheckedInBy, Ins, Comp, TPO,
        Spare,
        Jack, Brace, RegNo, MakeAndModel, ChassisNo, EngineCC, Mileage, EngineNo, EngineCode, Manual, Auto, Empty,
        Quarter, Half,
        ThreeQuarter, Full, PaintCode, ClientInstruction, Notes, IsComplete, Status
):
    with db_cursor() as cursor:
        # Insert into tbl_jobcarddetails
        query = """
            INSERT INTO tbl_jobcarddetails (
                ClientDetails, JobCardRef, ReceivedDate, DueDate, ExpDate, CheckedInBy,
                Ins, Comp, TPO, Spare, Jack, Brace, RegNo, MakeAndModel, ChassisNo,
                EngineCC, Mileage, EngineNo, EngineCode, Manual, Auto, `Empty`, `Quarter`,
                `Half`, `ThreeQuarter`, `Full`, PaintCode, ClientInstruction, Notes, IsComplete, Status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        values = (
            ClientDetails, JobCardRef, ReceivedDate, DueDate, ExpDate, CheckedInBy,
            Ins, Comp, TPO, Spare, Jack, Brace, RegNo, MakeAndModel, ChassisNo,
            EngineCC, Mileage, EngineNo, EngineCode, Manual, Auto, Empty, Quarter,
            Half, ThreeQuarter, Full, PaintCode, ClientInstruction, Notes, IsComplete, Status
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
            technicianDetails  # The technician
        )
        cursor.execute(query2, values2)


# Get job card id to assign in tbl_pendingassignedjobs
@anvil.server.callable()
def getJobCardID(jobCardRef):
    with db_cursor() as cursor:
        query = """
            SELECT ID FROM tbl_jobcarddetails 
            WHERE JobCardRef = %s 
        """
        cursor.execute(query, (jobCardRef,))
        result = cursor.fetchone()
        return result


@anvil.server.callable()
def getJobCardRef(valueID):
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
    with db_cursor() as cursor:
        query = """
        SELECT ID, MakeAndModel, JobCardRef, RegNo, DueDate, ClientInstruction, Status
        FROM tbl_jobcarddetails 
        WHERE Status IN (
            'Checked In', 'Create Quote', 'Confirm Quote',
            'In Service', 'Verify Task', 'Issue Invoice', 'Ready for Pickup'
        )
        ORDER BY DueDate DESC
        """
        cursor.execute(query)
        result = cursor.fetchall()

        jobcards = {}
        for r in result:
            # Clean up the ClientInstruction field
            instruction = r[5] or ""
            text_only = re.sub(r'<[^>]+>', '', instruction)
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]
            clean_instruction = "\n".join(lines)

            card = {
                "id": r[0],
                "make": r[1],
                "jobcardref": r[2],
                "plate": r[3],
                "date": r[4],
                "instruction": clean_instruction,
                "status": r[6]
            }

            jobcards.setdefault(r[6], []).append(card)

        return jobcards


@anvil.server.callable
def getTechnicianJobCards(status):
    with db_cursor() as cursor:
        query = """
        SELECT 
            tbl_jobcarddetails.ID, tbl_jobcarddetails.MakeAndModel, tbl_jobcarddetails.JobCardRef, 
            tbl_jobcarddetails.RegNo, tbl_jobcarddetails.DueDate, tbl_jobcarddetails.ClientInstruction, 
            tbl_jobcarddetails.Status, tbl_technicians.Fullname
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
        WHERE 
            Status = %s
        ORDER BY 
            DueDate DESC
        """
        cursor.execute(query, (status,))
        result = cursor.fetchall()

        jobcards = []
        for r in result:
            instruction = r[5] or ""
            text_only = re.sub(r'<[^>]+>', '', instruction)
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
                "technician": r[7]
            }

            jobcards.append(card)

        return jobcards


@anvil.server.callable
def getJobCardRefEditDetails():
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

@anvil.server.callable
def update_job_card_details(jobcardID,technicianDetails, ClientDetails, JobCardRef, ReceivedDate, DueDate, ExpDate,
                            CheckedInBy, Ins, Comp, TPO, Spare, Jack, Brace,  MakeAndModel,
                            EngineCC,  Mileage, EngineNo,  EngineCode,  Manual,  Auto,  Empty,  Quarter,  Half,
                            ThreeQuarter,  Full,  PaintCode, ClientInstruction,  Notes):
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_jobcarddetails
            SET
                ClientDetails = %s, JobCardRef = %s, ReceivedDate = %s,DueDate = %s,ExpDate = %s,CheckedInBy = %s,
                TPO = %s,Comp = %s,Spare = %s,Jack = %s, Brace = %s,MakeAndModel = %s,
                EngineCC = %s, Mileage = %s,EngineNo = %s,EngineCode = %s,Manual = %s, Auto = %s, `Empty` = %s,
                `Quarter` = %s,Half = %s, ThreeQuarter = %s, `Full` = %s, PaintCode = %s, ClientInstruction = %s,Notes = %s
            WHERE ID = %s
        """
        values = (ClientDetails, JobCardRef, ReceivedDate, DueDate, ExpDate, CheckedInBy,
            TPO, Comp, Spare, Jack, Brace, MakeAndModel,
            EngineCC, Mileage, EngineNo, EngineCode, Manual, Auto,
            Empty, Quarter, Half, ThreeQuarter, Full,
            PaintCode, ClientInstruction, Notes,jobcardID)

        cursor.execute(query, values)

        query2 = """
            UPDATE tbl_pendingassignedjobs 
            SET 
                TechnicianID=%s, DateAssigned=Now()
            WHERE JobCardRefID = %s
        """
        values2 = (technicianDetails,jobcardID)
        cursor.execute(query2, values2)

# ***************************************************Technician Details Section ************************************

@anvil.server.callable()
def saveTecnicianDefectsAndRequestedParts(jobcardref, defects, requiredparts):
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_techniciandefectsandrequestedparts (JobCardRefID, Defects, RequestedParts)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (jobcardref, defects, requiredparts))


@anvil.server.callable
def getJobCardDefects(id):
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
            text_only = re.sub(r'<[^>]+>', '', raw_instructions)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""


@anvil.server.callable()
def getRequestedParts(id):
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
            text_only = re.sub(r'<[^>]+>', '', raw_instructions)

            # Step 2: Split into lines, strip extra whitespace
            lines = [line.strip() for line in text_only.splitlines() if line.strip()]

            # Step 3: Return as clean multiline text
            return "\n".join(lines)
        else:
            return ""


@anvil.server.callable()
def updateJobCardStatus(jobcardref, status):
    with db_cursor() as cursor:
        query = """
                        UPDATE tbl_jobcarddetails 
                        SET Status = %s 
                        WHERE ID = %s;
                    """
        cursor.execute(query, (status, jobcardref))


# ***************************************************Car Parts Details Section ************************************
@anvil.server.callable()
def getCarPartNames():
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
def getCarPartNumberWithID(valueID):
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
    with db_cursor() as cursor:
        query = """
            SELECT Amount 
            FROM tbl_partssellingprice
            WHERE CarPartsNamesID = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        return result


# ***************************************************Quotation Details Section ************************************

@anvil.server.callable()
def getQuotationJobCardDetails():
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
def saveQuotationPartsAndServices(assignedDate, jobCardID, name, number, quantity, amount):
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_quotation (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount)
            VALUES (%s,%s,%s,%s, %s, %s)
        """
        cursor.execute(query, (assignedDate, jobCardID, name, number, quantity, amount))


@anvil.server.callable()
def get_quote_details_by_job_id(job_id):
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
            display_quantity_issued = "" if r[8] is None or not isinstance(r[8], (int, float,
                                                                                  decimal.Decimal)) else quantity_issued_val

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
                    "Total": total_calc  # This is now always a float or None
                }
            )

        return result


@anvil.server.callable
def fillQuotationInvoiceData(jobCardID, docType,logo_path: str = os.getenv("LOGO")) -> str:
    if docType == "Quotation":
        docTitle = "Quotation"
        vehicledetails = get_quote_details_by_job_id(jobCardID)
    elif docType == "InterimQuotation":
        docTitle = "Interim Quotation"
        vehicledetails = get_quote_details_by_job_id(jobCardID)
    elif docType == "Invoice":
        docTitle = "Invoice"
        vehicledetails = get_invoice_details_by_job_id(jobCardID)

    # Handle logo path - use absolute path or remove image entirely
    if logo_path and os.path.exists(logo_path):
        # Convert to absolute path
        logo_path = os.path.abspath(logo_path)
        # Convert to file:// URL for wkhtmltopdf
        logo_url = f"file:///{logo_path.replace(os.sep, '/')}"
        logo_img_tag = f'<img src="{logo_url}" alt="Company Logo" style="width: 100%; height: 100%; border-radius: 2px;" onerror="this.style.display=\'none\'; this.parentNode.innerHTML=\'LOGO\';">'
    else:
        # Just show LOGO text if no valid image path
        logo_img_tag = 'LOGO'


    # Calculate grand total
    sub_total = sum(float(item['Total']) for item in vehicledetails)
    for item in vehicledetails:
        if item['Item'] == 'Previous Balance':
            previous_balance = item['Amount']
            sub_total = sub_total - item['Amount'] #Get sub total without previous balance
            footer_total_details = f"""
                        <tr class="total-row">
                            <td colspan="4" style="text-align: right; font-weight: 500;">Sub Total</td>
                            <td style="font-weight: 500;">{sub_total:,.2f}</td>                    
                        </tr>
                        <tr class="total-row">
                            <td colspan="4" style="text-align: right; font-weight: 500;">Previous Balance</td>
                            <td style="font-weight: 500;">{previous_balance:,.2f}</td>
                        </tr>       
                """
        else:
            previous_balance = 0
            footer_total_details=''

    grand_total = sub_total + float(previous_balance)

    # Generate items table rows
    items_html = ""
    counter = 0
    for item in vehicledetails:
        counter = counter + 1
        if item["Amount"] == 0: #Implies To Be Confirmed
            textAmount = "TO BE CONFIRMED"
        else:
            textAmount = f"{item['Amount']:,.2f}"
        if item["Total"] == 0: #Implies To Be Confirmed
            textTotal = "TO BE CONFIRMED"
        else:
            textTotal = f"{item['Total']:,.2f}"

        #Do not display Previous balance in the table
        if item['Item'] != 'Previous Balance':

            items_html += f"""
                    <tr class="item-row">
                        <td>{counter}</td>
                        <td>{item['Item']}</td>
                        <td>{item['QuantityIssued']}</td>
                        <td>{textAmount}</td>
                        <td>{textTotal}</td>
                    </tr>"""

    if docType in ("Quotation", "InterimQuotation"):
        quotationNotes = """
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
        quotationNotes = """
                    <div class="notes-section">
                        <div class="notes-title">NOTES: </div>
                        <ol class="notes-list">
                            <li>Thank you for choosing BMW CENTER LIMITED</li>
                            <li>M-Pesa Paybill Number: 529914 \n
				                Account Number:   155393</li>
                            <li>Cheque Address to: BMW CENTER LIMITED</li>
                         </ol>
                    </div>
            """

        # Complete HTML template with fixed structure
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{docTitle}</title>
    <link href="https://fonts.googleapis.com/css2?family=Mozilla+Headline&display=swap" rel="stylesheet">
    <style>
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
                    <td colspan="4" style="text-align: right; font-weight: 500;">Grand Total</td>
                    <td style="font-weight: 500;">{grand_total:,.2f}</td>
                </tr>
                
            </tbody>
        </table>
    {quotationNotes} 
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
def createQuotationInvoicePdf(jobCardID, docType):
    try:
        docName = anvil.server.call('getQuotationInvoiceName', jobCardID)
        if docType == "Quotation":
            fileName = str(docName) + ' Quotation'
        elif docType == "InterimQuotation":
            fileName = str(docName) + ' Interim Quote'
        elif docType == "Invoice":
            fileName = str(docName) + ' Invoice'


        setting_options = {
            "encoding": "UTF-8",
            "custom-header": [('Accept-Encoding', 'gzip')],
            'page-size': 'A4',
            'orientation': 'Portrait',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'no-outline': False,
            'enable-local-file-access': None
        }

        html_string = fillQuotationInvoiceData(jobCardID, docType)
        pdfkit.from_string(html_string, fileName, options=setting_options, configuration=config)
        media_object = anvil.media.from_file(fileName, "application/pdf", name=fileName)
        return media_object

    except Exception as e:
        print("PDF generation failed:", str(e))
        raise


@anvil.server.callable()
def deleteFile(jobCardID, docType):
    docName = anvil.server.call('getQuotationInvoiceName', jobCardID)
    if docType == "Quotation":
        fileName = str(docName) + ' Quotation'
    elif docType == "InterimQuotation":
        fileName = str(docName) + ' Interim Quote'
    elif docType == "Invoice":
        fileName = str(docName) + ' Invoice'
    elif docType == "Payment":
        fileName = str(docName) + ' Payment'

    if os.path.exists(fileName):
        os.remove(fileName)
        print("File deleted successfully.")
    else:
        print("File does not exist.")


@anvil.server.callable()
def populate_confirmation_from_quote(jobcardID):
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
                "Amount": f"{float(r[3]):,.2f}"
            }
            for r in results
        ]


# ***************************************************Quotation Feedback Details Section ************************************

@anvil.server.callable()
def saveFullQuotationPartsAndServicesFeedback(assignedDate, jobCardID, remarks, items):
    with db_cursor() as cursor:
        # Step 1: Insert one feedback record
        cursor.execute("""
            INSERT INTO tbl_clientquotationfeedback (AssignedJobID, Remarks)
            VALUES (%s, %s)
        """, (jobCardID, remarks))

        # Step 2: Get the last inserted ID
        feedback_id = cursor.lastrowid

        # Step 3: Insert all items linked to the single feedback ID
        insert_item = """
            INSERT INTO tbl_quotationpartsandservicesfeedback 
            (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount, ClientQuotationFeedbackID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for item in items:
            cursor.execute(insert_item, (
                assignedDate,
                jobCardID,
                item['name'],
                item['number'],
                item['quantity'],
                item['amount'],
                feedback_id
            ))

        return {"status": "success", "feedback_id": feedback_id}


@anvil.server.callable()
def getClientQuotationFeedback(JobCardID):
    with db_cursor() as cursor:
        query = """
        SELECT ID FROM tbl_clientquotationfeedback WHERE AssignedJobID = %s
        """
        cursor.execute(query, (JobCardID,))
        result = cursor.fetchone()

        if not result:
            return 'No feedback found'

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

        if not result:
            return 'No feedback found'

        return [{"Name": row[0], "Number": row[1], "Quantity": row[2], "Amount": f"{float(row[3]):,.2f}"} for row in
                result]


# ***************************************************Verify Task  Details Section ************************************

@anvil.server.callable()
def saveConfirmationDetails(jobCardId, remarks, signature, dateCompleted):
    with db_cursor() as cursor:
        # Read binary content from Anvil media object
        signature_bytes = signature.get_bytes()

        query = """
            INSERT INTO tbl_completedjobcards (AssignedJobCardID , Remarks, Signature, DateCompleted)
            Values (%s, %s, %s, %s)
        """
        cursor.execute(query, (jobCardId, remarks, signature_bytes, dateCompleted))

        # Update job card to completed
        query2 = """
            UPDATE tbl_jobcarddetails SET tbl_jobcarddetails.IsComplete = 1
            WHERE ID = %s
        """
        cursor.execute(query2, (jobCardId,))


# ***************************************************Invoice Details Section ************************************
@anvil.server.callable()
def getInvoiceJobCardDetails():
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
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_invoices 
            (Date, AssignedJobID, Item, Part_No, QuantityIssued, Amount, Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for item in items:
            cursor.execute(query, (
                assignedDate,
                jobCardID,
                item['name'],
                item['number'],
                item['quantity'],
                item['amount'],
                "Pending"
            ))
        query2="""
            INSERT INTO tbl_assignedcarparts ( Date, AssignedJobID, CarPartID, QuantityIssued )
            VALUES (%s, %s, %s, %s)
        """
        for item in items:
            if item.get("CarPartID") is not None:
                cursor.execute(query2,(assignedDate,jobCardID,item.get("CarPartID"),item.get("quantity")
                        )
                )



@anvil.server.callable()
def get_invoice_details_by_job_id(job_id):
    with db_cursor() as cursor:
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
                    tbl_carpartnames.ID AS CarPartID   -- ✅ new column
                FROM 
                    (tbl_jobcarddetails 
                    INNER JOIN tbl_clientcontacts 
                        ON tbl_jobcarddetails.ClientDetails = tbl_clientcontacts.ID) 
                INNER JOIN tbl_invoices 
                    ON tbl_jobcarddetails.ID = tbl_invoices.AssignedJobID
                LEFT JOIN tbl_carpartnames   -- ✅ join to match PartNo
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
            display_quantity_issued = "" if r[8] is None or not isinstance(r[8], (int, float,
                                                                                  decimal.Decimal)) else quantity_issued_val

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
                    "PartNo":r[11],
                    "CarPartID": r[12],
                    "Total": total_calc  # This is now always a float or None
                }
            )

        return result


@anvil.server.callable()
def getPendingInvoices():
    with db_cursor() as cursor:
        query = """
            SELECT tbl_invoices.AssignedJobID, tbl_jobcarddetails.JobCardRef FROM tbl_invoices 
            INNER JOIN tbl_jobcarddetails ON tbl_invoices.AssignedJobID = tbl_jobcarddetails.ID 
            WHERE (((tbl_invoices.Status)="Pending")) 
            GROUP BY tbl_invoices.AssignedJobID
        """
        cursor.execute(query)
        result = cursor.fetchall()
        return [{"ID": r[0], "JobCardRef": r[1]} for r in result]


@anvil.server.callable()
def get_invoice_total_by_job_id(assigned_job_id):
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
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_invoices
            SET Status = 'Paid'
            WHERE AssignedJobID = %s
        """
        cursor.execute(query, (jobCardRefID,))


@anvil.server.callable()
def get_invoice_totals_and_counts_by_date(start_date, end_date):
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
            "Paid": {"count": 0, "total": 0.0}
        }

        for status, count, total in results:
            summary[status]["count"] = count
            summary[status]["total"] = float(total) if total else 0.0

        return summary

@anvil.server.callable()
def getJobCardRefInvoiceDetails(value):
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
                tbl_jobcarddetails.JobCardRef ASC;
        """

        like_value = f"%{value}%"
        cursor.execute(query, (like_value,))
        result = cursor.fetchall()

        # Return directly as list of tuples for a dropdown [(display_text, value), ...]
        return [(row[1], row[0]) for row in result]  # (JobCardRef, AssignedJobID)


@anvil.server.callable()
def updateInvoice(invoicedate, job_card_id, items):
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
                    item.get("Item"),
                    item.get("Part_No"),
                    item.get("QuantityIssued"),
                    item.get("Amount")
                )
            )
        query3 = """
            DELETE FROM tbl_assignedcarparts WHERE AssignedJobID = %s
        """
        cursor.execute(query3, (job_card_id,))
        
        query4="""
            INSERT INTO tbl_assignedcarparts ( Date, AssignedJobID, CarPartID, QuantityIssued )
            VALUES (%s, %s, %s, %s)
        """
        for item in items:
            if item.get("CarPartID") is not None:
                cursor.execute(query4,(invoicedate,job_card_id,item.get("CarPartID"),item.get("QuantityIssued")
                        )
                )

@anvil.server.callable()
def getInvoiceStatus(jobcardID):
    with db_cursor() as cursor:
        query = "SELECT DISTINCT Status FROM tbl_invoices WHERE AssignedJobID = %s"
        cursor.execute(query, (jobcardID,))
        result = cursor.fetchone()
        return result[0] if result else None

# ***************************************************Payment Details Section ************************************

@anvil.server.callable()
def get_previous_payment(invoice_id):
    with db_cursor() as cursor:
        query = """
            SELECT SUM(AmountPaid)
            FROM tbl_payments
            WHERE JobCardRefID = %s
        """
        cursor.execute(query, (invoice_id,))
        result = cursor.fetchone()
        return f"{float(result[0]):,.2f}" if result[0] is not None else 0.0


@anvil.server.callable()
def save_payment_details(paymentDate, jobCardRefID, paymentMode, amountPaid, discount, bal):
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_payments (Date, JobCardRefID, PaymentMode, AmountPaid, Discount, Balance)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (paymentDate, jobCardRefID, paymentMode, amountPaid, discount, bal))


@anvil.server.callable()
def getPaidPendingInvoices(status, start_date, end_date):
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
            display_quantity_issued = "" if row[4] is None or not isinstance(row[4], (int, float,
                                                                                      decimal.Decimal)) else quantity_issued_val

            # Calculate Total - ensuring we use the float versions for calculation
            total_calc = None
            if quantity_issued_val is None:  # If QuantityIssued was NULL/None from DB
                total_calc = amount_val
            elif amount_val is not None:  # Ensure Amount is not None for multiplication
                total_calc = round(quantity_issued_val * amount_val, 2)
            # If amount_val is None and quantity_issued_val is not None, total_calc would remain None

            result.append({
                'No': count,
                'Date': row[0],
                'JobCardRef': row[1],
                'Item': row[2],
                'PartNo': row[3],
                'Quantity': display_quantity_issued,
                'Amount': f"{float(amount_val):,.2f}",
                'Total': f"{float(total_calc):,.2f}"
            })

        return result


@anvil.server.callable()
def getPaymentsDetails(paymentID):
    with db_cursor() as cursor:
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
                                p.Balance
                            FROM
                                tbl_payments AS p
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
                            ORDER BY
                                p.Date DESC
                        """
        cursor.execute(query, (paymentID,))
        rows = cursor.fetchall()
        # Convert rows to a list of dictionaries
        result = [
            {
                "No": index + 1,
                "Date": row[0],
                "JobCardRef": row[1],
                "PaymentMode": row[2],
                "InvoiceAmount": f"{float(row[3]):,.2f}" if row[3] is not None else 0.0,
                "AmountPaid": f"{float(row[4]):,.2f}" if row[4] is not None else 0.0,
                "Discount": f"{float(row[5]):,.2f}" if row[5] is not None else 0.0,
                "Balance": f"{float(row[6]):,.2f}" if row[6] is not None else 0.0
            }
            for index, row in enumerate(rows)
        ]

        return result


@anvil.server.callable()
def get_payment_ref():
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

        result = [
            {
                "JobCardRef": row[0],
                "JobCardRefID": row[1]
            }
            for row in rows
        ]

        return result


@anvil.server.callable
def fillReportData(jobCardID, docType,
                   logo_path: str = os.getenv("LOGO")) -> str:
    if docType == "Payment":
        docTitle = "Payment Details"
        reportdetails = getPaymentsDetails(jobCardID)
        vehicledetails = get_invoice_details_by_job_id(jobCardID)

    # Handle logo path - use absolute path or remove image entirely
    if logo_path and os.path.exists(logo_path):
        # Convert to absolute path
        logo_path = os.path.abspath(logo_path)
        # Convert to file:// URL for wkhtmltopdf
        logo_url = f"file:///{logo_path.replace(os.sep, '/')}"
        logo_img_tag = f'<img src="{logo_url}" alt="Company Logo" style="width: 100%; height: 100%; border-radius: 2px;" onerror="this.style.display=\'none\'; this.parentNode.innerHTML=\'LOGO\';">'
    else:
        # Just show LOGO text if no valid image path
        logo_img_tag = 'LOGO'

    # Generate items table rows
    items_html = ""
    counter = 0
    for item in reportdetails:
        counter = counter + 1
        items_html += f"""
                    <tr class="item-row">
                        <td>{counter}</td>
                        <td>{item['Date']}</td>
                        <td>{item['JobCardRef']}</td>
                        <td>{item['PaymentMode']}</td>
                        <td>{item['InvoiceAmount']}</td>
                        <td>{item['AmountPaid']}</td>
                        <td>{item['Discount']}</td>
                        <td>{item['Balance']}</td>
                    </tr>"""

        # Complete HTML template with fixed structure
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{docTitle}</title>
    <link href="https://fonts.googleapis.com/css2?family=Mozilla+Headline&display=swap" rel="stylesheet">
    <style>
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
                    <th>Invoiced</th>
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
    try:
        docName = anvil.server.call('getQuotationInvoiceName', jobCardID)
        if docType == "Payment":
            fileName = str(docName) + ' Payment'

        setting_options = {
            "encoding": "UTF-8",
            "custom-header": [('Accept-Encoding', 'gzip')],
            'page-size': 'A4',
            'orientation': 'Portrait',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'no-outline': False,
            'enable-local-file-access': None
        }

        html_string = fillReportData(jobCardID, docType)
        pdfkit.from_string(html_string, fileName, options=setting_options, configuration=config)
        media_object = anvil.media.from_file(fileName, "application/pdf", name=fileName)
        return media_object

    except Exception as e:
        print("PDF generation failed:", str(e))
        raise


# ***************************************************Duplicate Phone Number Details Section ************************************

# Check for existing contacts
@anvil.server.callable()
def check_duplicate_contact(contacttype, phone):
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


# *************************************************** Interim Quotation Details Section ************************************

@anvil.server.callable()
def saveJobCardDetailsFromInterimQuotation(customer_ID, job_card_ref, received_date, due_date, check_in_staff, reg_no, make_and_model, chassis, engine_code, mileage):
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_jobcarddetails
            (ClientDetails, JobCardRef, ReceivedDate, DueDate, CheckedInBy, 
             RegNo, MakeAndModel, ChassisNo, EngineCode, Mileage, 
             Ins, ClientInstruction, Notes, IsComplete) 
            VALUES (%s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s)
        """
        cursor.execute(query, (
            customer_ID, job_card_ref, received_date, due_date, check_in_staff,
            reg_no, make_and_model, chassis, engine_code, mileage, 1,
            "None", "None", 1
        ))
        return cursor.lastrowid

@anvil.server.callable()
def saveInterimQuotationPartsAndServices(assignedDate, jobCardID, items):
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
            cursor.execute(query, (assignedDate, jobCardID, name, number, quantity, amount))

@anvil.server.callable()
def getInterimQuoteAndAmendedInvoiceStaff():
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


# *************************************************** Inventory Details Section ************************************

@anvil.server.callable()
def get_filtered_parts(part_filter=""):
    with db_cursor() as cursor:
        query = """
            WITH latest_stock AS (
                SELECT sp.CarPart, sp.UnitCost, sp.Date,
                       ROW_NUMBER() OVER (PARTITION BY sp.CarPart ORDER BY sp.ID DESC) AS rn
                FROM tbl_stockparts sp
            )
            SELECT 
                s.Name AS Supplier,
                cpn.Name,
                cpn.PartNo,
                cpn.OrderLevel AS `Reorder Level`,
                ls.UnitCost AS Cost,
                psp.Amount AS Selling,
                psp.SaleDiscount AS Discount,
                MAX(sp.Date) AS MaxOfDate
            FROM tbl_carpartnames cpn
            INNER JOIN tbl_partssellingprice psp 
                ON cpn.ID = psp.CarPartsNamesID
            INNER JOIN tbl_stockparts sp 
                ON cpn.ID = sp.CarPart
            INNER JOIN tbl_carpartssupplier s 
                ON cpn.CarPartsSupplierID = s.ID
            INNER JOIN latest_stock ls 
                ON ls.CarPart = cpn.ID AND ls.rn = 1
            WHERE cpn.Name LIKE %s OR cpn.PartNo LIKE %s
            GROUP BY 
                s.Name,
                cpn.Name,
                cpn.PartNo,
                cpn.OrderLevel,
                psp.Amount,
                psp.SaleDiscount,
                cpn.ID,
                ls.UnitCost
            ORDER BY cpn.Name;
        """

        like_filter = f"%{part_filter}%"
        cursor.execute(query, (like_filter, like_filter))
        rows = cursor.fetchall()

        result = []
        for count, row in enumerate(rows, start=1):
            result.append({
                "No": count,
                "Supplier": row[0],
                "Name": row[1],
                "PartNo": row[2],
                "ReorderLevel": row[3],
                "Cost": f"{float(row[4]):,.2f}" if row[4] is not None else None,
                "Selling": f"{float(row[5]):,.2f}" if row[5] is not None else None,
                "Discount": row[6],
                "MaxOfDate": row[7]
            })

        return result



@anvil.server.callable()
def search_car_parts_location(search_term=""):
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
            {
                "No": count,
                "Name": row[1],
                "PartNo": row[2],
                "Location": row[3]
            }
            for count, row in enumerate(rows, start=1)
        ]


@anvil.server.callable()
def missing_buying_prices(search_term=""):
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
                tbl_carpartnames.CarPartsSupplierID = tbl_carpartssupplier.ID
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
            result.append({
                "No": count,
                "Supplier":row[0],
                "Name": row[1],
                "PartNo": row[2],
                "Cost": f"{row[3]:,.2f}"
            })

        return result

@anvil.server.callable()
def get_buying_prices(search_term=""):
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
            INNER JOIN tbl_carpartssupplier s ON cp.CarPartsSupplierID = s.ID
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
                "NoOfUnits": row[5]
            }
            for idx, row in enumerate(rows, start=1)
        ]

        return result


@anvil.server.callable()
def get_buying_prices_by_partID(valueID):
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
                tbl_carpartnames.CarPartsSupplierID = tbl_carpartssupplier.ID
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
            result.append({
                "No": count,
                "Date":row[0],
                "Supplier":row[1],
                "Name": row[2],
                "PartNo": row[3],
                "Cost": f"{row[4]:,.2f}"
            })

        return result
    
@anvil.server.callable()
def missing_selling_prices(search_term=""):
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
                        tbl_carpartnames.CarPartsSupplierID = tbl_carpartssupplier.ID
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
            result.append({
                "No": count,
                "Supplier":row[0],
                "Name": row[1],
                "PartNo": row[2],
                "Amount": f"{row[3]:,.2f}",
                "Discount": None if row[4] is None else f"{float(row[4]):,.2f}"
            })

        return result

@anvil.server.callable()
def get_selling_prices(search_term=""):
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
                        tbl_carpartnames.CarPartsSupplierID = tbl_carpartssupplier.ID
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
            result.append({
                "No": count,
                "Supplier":row[0],
                "Name": row[1],
                "PartNo": row[2],
                "Amount": f"{row[3]:,.2f}",
                "Discount": None if row[4] is None else f"{float(row[4]):,.2f}"
            })

        return result

@anvil.server.callable()
def updatePrice(priceType, newPrice, discount,partNo):
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

@anvil.server.callable
def getPriorityList(regNo=""):
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
            results.append({
                "Name": row[1],
                "Number": row[2],
                "Quantity": row[3],
                "Amount": f"{float(row[4]):,.2f}",
                "Priority": row[5]
            })

        return results

@anvil.server.callable()
def deleteCurrentPriority(regNo):
    with db_cursor() as cursor:
        query = """
            DELETE FROM tbl_repairpriorities WHERE RegNo = %s
        """
        cursor.execute(query, (regNo,))


@anvil.server.callable()
def savePriority(assignedDate, regNo, name, number, quantity, amount, priority):
    with db_cursor() as cursor:
        query = """
            INSERT INTO 
                tbl_repairpriorities(Date,RegNo,PartName,PartNumber,Quantity,Amount,Priority) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (assignedDate, regNo, name, number, quantity, amount, priority))

@anvil.server.callable()
def get_priority_list(regNo):
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
            display_quantity_issued = "" if r[4] is None or not isinstance(r[4], (int, float, decimal.Decimal)) else quantity_issued_val

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
                "Priority": r[6]
            }

            if str(r[6]).strip().lower() == "urgent":
                urgent.append(entry)
            elif str(r[6]).strip().lower() == "can wait":
                can_wait.append(entry)

        return {
            "Urgent": urgent,
            "CanWait": can_wait
        }


@anvil.server.callable()
def fillFormData(regNo, docType,logo_path: str = os.getenv("LOGO")) -> str:
    if docType == "Priority":
        docTitle = "Repair Priority List"
        priorityDetails = get_priority_list(regNo)
        #Get Date and RegNo
        if priorityDetails["Urgent"]:
            currentDate = priorityDetails["Urgent"][0]['Date']
        else:
            currentDate = priorityDetails["CanWait"][0]['Date']

    # Handle logo path - use absolute path or remove image entirely
    if logo_path and os.path.exists(logo_path):
        # Convert to absolute path
        logo_path = os.path.abspath(logo_path)
        # Convert to file:// URL for wkhtmltopdf
        logo_url = f"file:///{logo_path.replace(os.sep, '/')}"
        logo_img_tag = f'<img src="{logo_url}" alt="Company Logo" style="width: 100%; height: 100%; border-radius: 2px;" onerror="this.style.display=\'none\'; this.parentNode.innerHTML=\'LOGO\';">'
    else:
        # Just show LOGO text if no valid image path
        logo_img_tag = 'LOGO'

    # Generate items table rows
    urgent_header = "Urgent"
    items_html_urgent = ""
    # Calculate sub total
    sub_total_urgent = sum(float(item['Total']) for item in priorityDetails["Urgent"])
    canwait_header = "Can Wait"
    items_html_canwait = ""
    # Calculate sub total
    sub_total_canwait = sum(float(item['Total']) for item in priorityDetails["CanWait"])

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
    <link href="https://fonts.googleapis.com/css2?family=Mozilla+Headline&display=swap" rel="stylesheet">
    <style>
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
def downloadRevisionPdfForm(regNo, docType):
    try:
        docName = regNo
        if docType == "Priority":
            fileName = str(docName) + ' Priority'
        elif docType == "Brand":
            fileName = str(docName) + ' Brand'

        setting_options = {
            "encoding": "UTF-8",
            "custom-header": [('Accept-Encoding', 'gzip')],
            'page-size': 'A4',
            'orientation': 'Portrait',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'no-outline': False,
            'enable-local-file-access': None
        }

        if docType == "Priority":
            html_string = fillFormData(regNo, docType)
        elif docType == "Brand":
            html_string = fillBrandComparisonFormData(regNo, docType)

        pdfkit.from_string(html_string, fileName, options=setting_options, configuration=config)
        media_object = anvil.media.from_file(fileName, "application/pdf", name=fileName)
        return media_object

    except Exception as e:
        print("PDF generation failed:", str(e))
        raise

@anvil.server.callable()
def deleteRevisionFile(regNo, docType):
    # Construct file name based on docType
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

@anvil.server.callable
def getBrandComparisonList(regNo=""):
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
            results.append({
                "Name": row[1],
                "Number": row[2],
                "Quantity": row[3],
                "Amount": "TO BE CONFIRMED" if float(row[4]) == 0 else f"{float(row[4]):,.2f}",
                "GroupID": row[5]
            })

        return results

@anvil.server.callable()
def get_brand_list(regNo):
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
            display_quantity_issued = "" if r[4] is None or not isinstance(r[4], (int, float, decimal.Decimal)) else quantity_issued_val

            total_calc = None
            if quantity_issued_val is None:
                total_calc = amount_val
            elif amount_val is not None:
                total_calc = round(quantity_issued_val * amount_val, 2)

            entry.append( {
                "No": count,
                "Date": r[0],
                "RegNo": r[1],
                "PartName": r[2],
                "PartNumber": r[3],
                "Quantity": display_quantity_issued,
                "Amount": amount_val,
                "Total": total_calc,
                "GroupID": r[6]
            })

        return entry


@anvil.server.callable()
def fillBrandComparisonFormData(regNo, docType,
                 logo_path: str = os.getenv("LOGO")) -> str:
    if docType == "Brand":
        docTitle = "Brand Comparison List"
        comparisonDetails = get_brand_list(regNo)

    # Handle logo path - use absolute path or remove image entirely
    if logo_path and os.path.exists(logo_path):
        # Convert to absolute path
        logo_path = os.path.abspath(logo_path)
        # Convert to file:// URL for wkhtmltopdf
        logo_url = f"file:///{logo_path.replace(os.sep, '/')}"
        logo_img_tag = f'<img src="{logo_url}" alt="Company Logo" style="width: 100%; height: 100%; border-radius: 2px;" onerror="this.style.display=\'none\'; this.parentNode.innerHTML=\'LOGO\';">'
    else:
        # Just show LOGO text if no valid image path
        logo_img_tag = 'LOGO'

    currentDate = comparisonDetails[0]['Date']

    # Calculate sub total
    #sub_total = sum(float(item['Total']) for item in comparisonDetails)

    # Group items by GroupID
    grouped_data = defaultdict(list)
    for item in comparisonDetails:
        grouped_data[item['GroupID']].append(item)

    items_html = ""
    grand_total = 0

    for group_id, group_items in grouped_data.items():
        group_total = sum(item['Total'] or 0 for item in group_items)
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
                    <td>{item['No']}</td>
                    <td>{item['PartName']}</td>
                    <td>{item['Quantity']}</td>
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
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{docTitle}</title>
    <link href="https://fonts.googleapis.com/css2?family=Mozilla+Headline&display=swap" rel="stylesheet">
    <style>
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
    with db_cursor() as cursor:
        query = """
            DELETE FROM tbl_brandcomparison WHERE RegNo = %s
        """
        cursor.execute(query, (regNo,))

@anvil.server.callable()
def saveBrand(assignedDate, regNo, name, number, quantity, amount, groupid):
    with db_cursor() as cursor:
        query = """
            INSERT INTO 
                tbl_brandcomparison(Date,RegNo,PartName,PartNumber,Quantity,Amount,GroupID) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (assignedDate, regNo, name, number, quantity, amount, groupid))

# *************************************************** Location Details Section ************************************

@anvil.server.callable()
def getLocation():
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
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_carpartslocation (Location) VALUES (%s)
        """
        cursor.execute(query, (locationName,))

@anvil.server.callable()
def getLocationName(valueID):
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
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_carpartssupplier (Name, Phone) VALUES (%s, %s)
        """
        cursor.execute(query, (supplierName, supplierPhone))

@anvil.server.callable()
def getSupplierDetails(supplierID):
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
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_carpartssupplier
            SET Name = %s, Phone = %s
            WHERE ID = %s
        """
        cursor.execute(query, (supplierName, supplierPhone, supplierID))

# *************************************************** New Car Parts Details Section ************************************

@anvil.server.callable()
def addNewParts(purchaseDate, partName, partNumber, locationID, supplierID, units, buyingPrice, sellingPrice,discountPrice, reorderLevel):
    with db_cursor() as cursor:
        query = """
            INSERT INTO 
            tbl_carpartnames(CarPartsSupplierID,Name,PartNo,OrderLevel,Location) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query,(supplierID, partName, partNumber,reorderLevel,locationID))

        partID = cursor.lastrowid

        query2 = """
            INSERT INTO 
            tbl_partssellingprice(SetPriceDate, CarPartsNamesID, Amount, SaleDiscount) 
            VALUES (%s,%s,%s,%s)
        """
        cursor.execute(query2, (purchaseDate, partID, sellingPrice, discountPrice))

        query3 = """
          INSERT INTO 
          tbl_stockparts(Date, CarPart, NoOfUnits, UnitCost, Narration) 
          VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query3, (purchaseDate, partID, units, buyingPrice, " "))

@anvil.server.callable()
def check_duplicate_number(number):
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
    with db_cursor() as cursor:
        query = """
            SELECT 
                Max(tbl_stockparts.Date), Max(tbl_stockparts.NoOfUnits), Max(tbl_stockparts.UnitCost), 
                tbl_carpartnames.CarPartsSupplierID, tbl_carpartnames.Name, tbl_carpartnames.PartNo, 
                tbl_carpartnames.OrderLevel, tbl_carpartnames.Location 
            FROM 
                tbl_carpartnames 
            INNER JOIN 
                tbl_stockparts 
            ON 
                tbl_carpartnames.ID = tbl_stockparts.CarPart 
            WHERE tbl_carpartnames.ID = %s
        """
        cursor.execute(query, (id,))
        row = cursor.fetchone()

    if row:
        columns = ["Date", "NoOfUnits", "UnitCost","CarPartsSupplierID", "Name", "PartNo", "OrderLevel", "Location"]
        return dict(zip(columns, row))
    else:
        return None

@anvil.server.callable()
def getPartsSellingDetailsID(valueID):
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
def updateNewParts(purchaseDate,partName,partNumber,locationID,supplierID,units,buyingPrice,sellingPrice,discountPrice,reorderLevel,valueID):
    with db_cursor() as cursor:
        query = """
                    UPDATE tbl_carpartnames
                    SET 
                        CarPartsSupplierID = %s,
                        Name = %s,
                        PartNo = %s,
                        OrderLevel = %s,
                        Location = %s 
                    WHERE ID = %s
                """
        cursor.execute(query, (supplierID, partName, partNumber, reorderLevel, locationID, valueID))

        query2 = """
                    UPDATE tbl_partssellingprice
                    SET 
                        SetPriceDate = %s, 
                        CarPartsNamesID = %s, 
                        Amount = %s, 
                        SaleDiscount = %s 
                    WHERE CarPartsNamesID = %s
                """
        cursor.execute(query2, (purchaseDate, valueID, sellingPrice, discountPrice, valueID))

        query3 = """
                  UPDATE tbl_stockparts
                  SET 
                    Date = %s, 
                    CarPart = %s, 
                    NoOfUnits = %s, 
                    UnitCost = %s
                 WHERE CarPart = %s 
                """
        cursor.execute(query3, (purchaseDate, valueID, units, buyingPrice, valueID))

@anvil.server.callable()
def addStock(additionDate, partID, no_of_units, unit_cost):
    with db_cursor() as cursor:
        query = """
            INSERT INTO 
                tbl_stockparts(Date, CarPart, NoOfUnits, UnitCost, Narration) 
            VALUES  
                (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (additionDate,partID, no_of_units,unit_cost, ""))


# *************************************************** Stock Balance Details Section ************************************

@anvil.server.callable
def get_car_parts_summary(search_term=""):
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
                SELECT *
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
                "TotalIssued": row[4],
                "LatestStockTake": row[5],
                "TotalStock": row[7],
                "StockBalance": row[8],
                "BelowOrderLevel": row[9]
            }
            result.append(row_data)

        return result


# ***************************************************Car Parts Used Section ************************************

@anvil.server.callable()
def get_car_parts_used(job_card_id):
    with db_cursor() as cursor:
        if job_card_id is None:
            query = """
                SELECT 
                    tbl_assignedcarparts.Date, tbl_jobcarddetails.JobCardRef, tbl_carpartnames.Name, tbl_carpartnames.PartNo, 
                    tbl_assignedcarparts.QuantityIssued
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
                    tbl_assignedcarparts.QuantityIssued
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
                "Quantity": row[4]
            }
            result.append(row_data)

        return result

@anvil.server.callable()
def get_job_card_from_car_parts_used(search_term):
    with db_cursor() as cursor:
        query = """
            SELECT
                tbl_assignedcarparts.Date,
                tbl_jobcarddetails.JobCardRef,
                tbl_carpartnames.Name,
                tbl_carpartnames.PartNo,
                tbl_assignedcarparts.QuantityIssued
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
            result.append({
                "No": idx,
                "AssignedDate": row[0],
                "JobCardRef": row[1],
                "PartName": row[2],
                "PartNo": row[3],
                "Quantity": row[4]
            })
        return result

# ***************************************************Assigned JobCard Details Section ************************************

@anvil.server.callable()
def get_assigned_jobs(startDate, endDate, technicianID):
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

        elif startDate is None and endDate  is None and technicianID is not None:
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
            result.append({
                "No": idx,
                "ReceivedDate": row[0],
                "JobCardRef": row[1],
                "Technician": row[2],
                "InvoicedAmount": f"{row[3]:,.2f}",
                "LabourAmount": f"{row[4]:,.2f}",
                "MakeAndModel": row[5]
            })
        return result
    
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
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Add headers
    ws.append(headers)
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
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

@anvil.server.callable
def export_assigned_jobcards(rows):
    headers = [
        "No", "Received Date", "Job Card Ref", "Technician",
        "Invoiced Amount", "Labour Amount", "Make and Model"
    ]
    
    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append({
            "No": i,
            "ReceivedDate": row.get("ReceivedDate", ""),
            "JobCardRef": row.get("JobCardRef", ""),
            "Technician": row.get("Technician", ""),
            "InvoicedAmount": row.get("InvoicedAmount", ""),
            "LabourAmount": row.get("LabourAmount", ""),
            "MakeAndModel": row.get("MakeAndModel", "")
        })

    return make_excel(headers, processed_rows, filename="assigned_jobcards.xlsx", sheet_name="Jobcards")

@anvil.server.callable
def export_missing_buying_prices(rows):
    headers = [
        "No", "Supplier", "Name", "PartNo",
        "Buying Price"
    ]
    
    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append({
            "No": i,
            "Supplier": row.get("Supplier", ""),
            "Name": row.get("Name", ""),
            "PartNo": row.get("PartNo", ""),
            "Cost": row.get("BuyingPrice", "")
        })

    return make_excel(headers, processed_rows, filename="missing_buying_prices.xlsx", sheet_name="Buying Prices")

@anvil.server.callable
def export_missing_selling_prices(rows):
    headers = [
        "No", "Supplier", "Name", "PartNo",
        "Selling Price", "Discount Price"
    ]
    
    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append({
            "No": i,
            "Supplier": row.get("Supplier", ""),
            "Name": row.get("Name", ""),
            "PartNo": row.get("PartNo", ""),
            "Amount": row.get("Amount", ""),
            "Discount": row.get("Discount", "")
        })

    return make_excel(headers, processed_rows, filename="missing_selling_prices.xlsx", sheet_name="Selling Prices")

@anvil.server.callable
def export_client_payment_details(rows):
    headers = [
        "No", "JobReceivedDate","JobCardRef", "Fullname",
        "Phone", "TotalPaid", "Discount", "Balance"
    ]
    
    # Transform into list-of-dicts or list-of-lists
    processed_rows = []
    for i, row in enumerate(rows, start=1):
        processed_rows.append({
            "No": i,
            "JobReceivedDate": row.get("JobReceivedDate", ""),
            "JobCardRef": row.get("JobCardRef", ""),
            "Fullname": row.get("Fullname", ""),
            "Phone": row.get("Phone", ""),
            "TotalPaid": row.get('TotalPaid', 0),
            "Discount": row.get('Discount', 0),
            "Balance": row.get('Balance', 0)
        })

    return make_excel(headers, processed_rows, filename="client_payment_details.xlsx", sheet_name="Client Payments")

# *************************************************** Users Section ************************************

@anvil.server.callable()
def getUsers():
    with db_cursor() as cursor:
        rows = app_tables.users.search()
        result = []
        for i, row in enumerate(rows, start=1):
            def fmt_date(val):
                if val:
                    if hasattr(val, "tzinfo") and val.tzinfo:  # remove timezone if exists
                        val = val.replace(tzinfo=None)
                    return val.strftime("%Y-%m-%d %H:%M:%S")
                return None
            
            cursor.execute("SELECT Roles FROM tbl_roles WHERE ID = %s", (row["role_id"],))
            role = cursor.fetchone()
            
            result.append({
                "No": i,    
                "email": row["email"],
                "last_login": fmt_date(row["last_login"]),
                "signed_up": fmt_date(row["signed_up"]),
                "role": role[0] if role else None,
                "enabled": "Yes" if row["enabled"] else "No",
            })
        return result

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
            params.append(f"%{jobcard_ref}%")   # <-- partial match

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
        output.append({
            "No": no,
            "ID": r["ID"],
            "ReceivedDate": r["ReceivedDate"],
            "JobCardRef": r["JobCardRef"],
            "QuotationTotal": f"{float(r["QuotationTotal"] or 0):,.2f}",
            "InvoiceTotal": f"{float(r["InvoiceTotal"] or 0):,.2f}"
        })

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

    with db_cursor() as cursor:
        query = """
            SELECT 
                c.Fullname,
                c.Phone,
                j.JobCardRef,
                j.ReceivedDate,
                SUM(p.AmountPaid) AS TotalPaid,
                MAX(p.Discount)   AS Discount,
                MAX(p.Balance)    AS Balance
            FROM tbl_payments p
            INNER JOIN tbl_jobcarddetails j ON j.ID = p.JobCardRefID
            INNER JOIN tbl_clientcontacts c ON c.ID = j.ClientDetails
            WHERE 1=1
        """

        params = []

        # Optional search filter
        if search_term:
            query += " AND (c.Fullname LIKE %s OR c.Phone LIKE %s OR j.RegNo LIKE %s)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

        # Optional date filters
        if start_date and end_date:
            query += " AND j.ReceivedDate BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND j.ReceivedDate >= %s"
            params.append(start_date)
        elif end_date:
            query += " AND j.ReceivedDate <= %s"
            params.append(end_date)

        query += """
            GROUP BY c.Fullname, c.Phone, j.JobCardRef, j.ReceivedDate, j.ID
            ORDER BY j.ReceivedDate DESC
        """

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cols = [col[0] for col in cursor.description]

    # Convert rows to dicts and add No
    results = []
    for no, tup in enumerate(rows, start=1):
        r = dict(zip(cols, tup))
        results.append({
            "No": no,
            "JobReceivedDate": r["ReceivedDate"].strftime("%Y-%m-%d") if r["ReceivedDate"] else None,
            "JobCardRef": r["JobCardRef"],
            "Fullname": r["Fullname"],
            "Phone": r["Phone"],
            "TotalPaid": f"{float(r['TotalPaid'] or 0):,.2f}",
            "Discount": f"{float(r['Discount'] or 0):,.2f}",
            "Balance": f"{float(r['Balance'] or 0):,.2f}"
        })

    return results

# *************************************************** Roles Section ************************************

@anvil.server.callable()
def listRoles():
    with db_cursor() as cursor:
        query = "SELECT Roles, Description FROM tbl_roles ORDER BY Roles"
        cursor.execute(query)
        rows = cursor.fetchall()
        result = [{"Roles": row[0], "Description": row[1]} for row in rows]
        return result

@anvil.server.callable()
def duplicateRole(role, description):
    with db_cursor() as cursor:
        # Check if a role with the same name already exists
        cursor.execute("SELECT ID, Roles, Description FROM tbl_roles WHERE Roles = %s", (role,))
        existing = cursor.fetchone()

        if existing:
            # Duplicate exists → don’t insert
            return {"status": "duplicate", "id": existing[0], "role": existing[1], "description": existing[2]}
        
        # If not found, insert new
        query = "INSERT INTO tbl_roles (Roles, Description) VALUES (%s, %s)"
        cursor.execute(query, (role, description))
        return {"status": "inserted", "id": cursor.lastrowid, "role": role, "description": description}


@anvil.server.callable()
def getRoles():
    with db_cursor() as cursor:
        query = "SELECT ID, Roles FROM tbl_roles ORDER BY Roles"
        cursor.execute(query)
        rows = cursor.fetchall()
        result = [(row[1], row[0]) for row in rows]
        return result

@anvil.server.callable
def save_user_permissions(role_id, permissions_dict):
    with db_cursor() as cursor:
        # Delete old permissions first
        cursor.execute("DELETE FROM tbl_userpermissions WHERE RoleID = %s", (role_id,))

        # Insert new permissions
        for section, data in permissions_dict.items():
            # Save main section permission
            cursor.execute(
                """
                INSERT INTO tbl_userpermissions (RoleID, Section, SubSection, Allowed)
                VALUES (%s, %s, %s, %s)
                """,
                (role_id, section, None, int(data["main"]))
            )

            # Save each sub permission
            for sub, allowed in data["subs"].items():
                cursor.execute(
                    """
                    INSERT INTO tbl_userpermissions (RoleID, Section, SubSection, Allowed)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (role_id, section, sub, int(allowed))
                )

# *************************************************** Get User Permissions Section ************************************
@anvil.server.callable
def get_user_permissions(role_id):
    with db_cursor() as cursor:
        query = """
            SELECT Section, SubSection, Allowed
            FROM tbl_userpermissions
            WHERE RoleID = %s
        """
        cursor.execute(query, (role_id,))
        rows = cursor.fetchall()

        permissions = {}

        for section, subsection, allowed in rows:
            if section not in permissions:
                permissions[section] = {"main": False, "subs": {}}

            if subsection is None or subsection == "":
                # This is a main section permission
                permissions[section]["main"] = bool(allowed)
            else:
                # This is a sub-section permission
                permissions[section]["subs"][subsection] = bool(allowed)

        return permissions


# *************************************************** Edit User Account Section ************************************
@anvil.server.callable()
def get_account_roles():
    with db_cursor() as cursor:
        query = "SELECT ID, Roles FROM tbl_roles ORDER BY Roles ASC"
        cursor.execute(query)
        rows = cursor.fetchall()

    # Return as list of tuples (label, value) for dropdown
    return [(row[1], row[0]) for row in rows]

@anvil.server.callable()
def get_role_id(role_name: str):
    with db_cursor() as cursor:
        query = "SELECT ID FROM tbl_roles WHERE Roles = %s"
        cursor.execute(query, (role_name,))
        row = cursor.fetchone()

    return row[0] if row else None

@anvil.server.callable()
def update_user(email, new_email, enabled, role_id):
    
    user = app_tables.users.get(email=email)
    if not user:
        raise Exception(f"No user found with email: {email}")

    updates = {}
    if new_email is not None:
        updates["email"] = new_email
    if enabled is not None:
        updates["enabled"] = enabled
    if role_id is not None:
        updates["role_id"] = role_id

    if updates:
        user.update(**updates)

    return f"User {email} updated successfully."


@anvil.server.callable()
def reset_password(email, new_password):
    """Directly set a new password for a user (admin only)."""
    user = app_tables.users.get(email=email)
    if not user:
        raise Exception("No user found with that email.")

    # Use Anvil's internal function to set password
    anvil.users.force_change_password(user, new_password)
    return f"Password reset successfully for {email}"

# *************************************************** Get Roles And Permissions In HTML Format Section ************************************

@anvil.server.callable
def get_roles_permissions_html():
    html = """
    <style>
      body {
        font-family: "Mozilla Headline", Arial, Helvetica, sans-serif;
        font-size: 16px;
      }
      table {
        border-collapse: collapse;
        width: 100%;
        margin-top: 10px;
      }
      td {
        padding: 6px 12px;
        vertical-align: top;
        border: 1px solid #ccc;
      }
      tr:nth-child(even) {
        background-color: #f9f9f9;
      }
      .role {
        font-weight: 700;
        font-size: 18px;
        color: #2c3e50;
        background-color: #e6f0ff;
      }
      .section {
        font-weight: 600;
        color: #34495e;
        padding-left: 20px;
        background-color: #f2f6fc;
      }
      .subsection {
        color: #555;
        padding-left: 40px;
      }
      .allowed {
        padding-left: 60px;
        font-style: italic;
      }
    </style>
    <table>
    """

    sections_without_subs = {"JOB CARD", "TRACKER", "PAYMENT", "RESET"}

    with db_cursor() as cursor:
        query = """
            SELECT 
                r.Roles,
                u.Section,
                u.SubSection,
                u.Allowed,
                CASE u.Section
                    WHEN 'CONTACT'   THEN 1
                    WHEN 'JOB CARD'  THEN 2
                    WHEN 'WORKFLOW'  THEN 3
                    WHEN 'TRACKER'   THEN 4
                    WHEN 'REVISION'  THEN 5
                    WHEN 'PAYMENT'   THEN 6
                    WHEN 'INVENTORY' THEN 7
                    WHEN 'REPORTS'   THEN 8
                    WHEN 'SETTINGS'  THEN 9
                    WHEN 'RESET'  THEN 10
                    ELSE 999
                END AS section_order
            FROM tbl_roles r
            JOIN tbl_userpermissions u
              ON r.ID = u.RoleID
            ORDER BY
                r.Roles,
                section_order,
                u.SubSection
        """
        cursor.execute(query)
        rows = cursor.fetchall()

    # Build HTML hierarchy
    current_role = None
    current_section = None

    for role, section, subsection, allowed, _ in rows:
        if role != current_role:
            html += f'<tr><td class="role" colspan="2">Role: {role}</td></tr>'
            current_role = role
            current_section = None

        if section != current_section:
            html += f'<tr><td class="section" colspan="2">{section}</td></tr>'
            current_section = section

        # Handle sections without subsections
        if section in sections_without_subs:
            if int(allowed) == 1:
                html += '<tr><td class="allowed">Allowed</td><td><span style="color:green;">&#10004;</span></td></tr>'
            else:
                html += '<tr><td class="allowed">Allowed</td><td><span style="color:red;">&#10008;</span></td></tr>'
        else:
            # Normal subsection logic
            if subsection and subsection != "None":
                html += f'<tr><td class="subsection">{subsection}</td>'
                if int(allowed) == 1:
                    html += '<td><span style="color:green;">&#10004;</span></td></tr>'
                else:
                    html += '<td><span style="color:red;">&#10008;</span></td></tr>'

    html += "</table>"
    return html

# *************************************************** Resolve Part Number from Barcode Section ************************************
@anvil.server.callable
def resolve_part(barcode_or_partno):
    with db_cursor() as cursor:
        # 1. Check in tbl_carpartnames.PartNo
        cursor.execute("SELECT PartNo, Name FROM tbl_carpartnames WHERE PartNo = %s", (barcode_or_partno,))
        row = cursor.fetchone()
        if row:
            return {"PartNo": row[0], "Name": row[1]}

        # 2. Check in tbl_barcodepartnomapping.Barcode
        cursor.execute("SELECT PartNo FROM tbl_barcodepartnomapping WHERE Barcode = %s", (barcode_or_partno,))
        row = cursor.fetchone()
        if row:
            partno = row[0]
            # lookup in carpartnames
            cursor.execute("SELECT PartNo, Name FROM tbl_carpartnames WHERE PartNo = %s", (partno,))
            carpart = cursor.fetchone()
            if carpart:
                return {"PartNo": carpart[0], "Name": carpart[1]}

        # Not found
        return None

@anvil.server.callable()
def saveBarcodePartNo(barcode, partno):
    with db_cursor() as cursor:
        # Insert new mapping
        cursor.execute(
            "INSERT INTO tbl_barcodepartnomapping (Barcode, PartNo) VALUES (%s, %s)",
            (barcode, partno)
        )
        return f"Barcode '{barcode}' is mapped to PartNo '{partno}'."
    
# *************************************************** Stocktake Harmonization Section ************************************

@anvil.server.callable
def save_stocktake(repeating_panel_data):
    """
    repeating_panel_data is expected to be a list of dicts:
    [
        {"PartNo": "ABC123", "Name": "Brake Pad", "Quantity": 20},
        {"PartNo": "XYZ456", "Name": "Oil Filter", "Quantity": 15},
        ...
    ]
    """
    with db_cursor() as cursor:
        for item in repeating_panel_data:
            part_no = item["PartNo"]
            quantity = int(item["Quantity"])

            # 1. Get CarPartName info
            cursor.execute("""
                SELECT cp.ID, cp.Name, cp.PartNo, cp.OrderLevel, cl.Location
                FROM tbl_carpartnames cp
                LEFT JOIN tbl_carpartslocation cl ON cp.Location = cl.ID
                WHERE cp.PartNo = %s
            """, (part_no,))
            result = cursor.fetchone()
            if not result:
                continue
            carpart_id, carpart_name, part_number, reorder_level, location = result

            # 2. Get TotalStock and TotalIssued
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(sp.NoOfUnits), 0) AS TotalStock,
                    COALESCE(i.TotalIssued, 0) AS TotalIssued
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
            total_stock, total_issued = (stock_info if stock_info else (0, 0))

            # 3. Balance and Variance
            balance = total_stock - total_issued
            variance = quantity - balance

            # 4. Comment logic
            if quantity < balance:
                comment = "System Count > Actual Count"
            elif quantity > balance:
                comment = "Actual Count > System Count"
            else:
                comment = "Stock Balanced"

            # 5. Insert/Update tbl_stocktakeharmonized (harmonized values)
            cursor.execute("""
                INSERT INTO tbl_stocktakeharmonized
                    (StockTakeDate, CarPartNameID, HarmornizedValue)
                VALUES (CURDATE(), %s, %s)
                ON DUPLICATE KEY UPDATE
                    HarmornizedValue = VALUES(HarmornizedValue)
            """, (carpart_id, variance))

            # 6. Insert/Update tbl_finalcapturedstocktaking (daily unique)
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
            """, (
                carpart_name,
                part_number,
                reorder_level,
                location,
                balance,
                quantity,
                variance,
                comment
            ))

    return "Stocktake saved/updated successfully"

