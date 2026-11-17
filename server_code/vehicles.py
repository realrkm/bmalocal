from ._common import *

# ***************************************************Car Details Section ************************************


@anvil.server.callable()
def getCarRegistration():
    _get_current_user()
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


@anvil.server.callable()
def getCarRegistrationWithPartlyDetails(valueReg):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT MAX(ID) AS LastOfID, RegNo
            FROM tbl_jobcarddetails
            WHERE RegNo LIKE %s
            GROUP BY RegNo
            ORDER BY RegNo ASC
        """
        cursor.execute(query, (f"%{valueReg}%",))
        result = cursor.fetchall()

        # Return a list formatted for a DropDown in Anvil
        return [(row[1], row[0]) for row in result]  

@anvil.server.callable()
def get_car_details(search_term=None, limit=200):
    # Use table aliases (c and j) to make the query cleaner
    _get_current_user()
    query = """
        SELECT 
            c.Fullname, 
            c.Phone, 
            j.RegNo, 
            j.ChassisNo,
            j.ReceivedDate,
            j.JobCardRef,
            j.MakeAndModel
        FROM tbl_clientcontacts c
        INNER JOIN tbl_jobcarddetails j 
            ON c.ID = j.ClientDetails
    """
    params = []
    
    # Dynamically add the WHERE clause only if a search term is provided
    if search_term:
        query += """
            WHERE c.Fullname LIKE %s 
               OR c.Phone LIKE %s 
               OR j.RegNo LIKE %s 
               OR j.ChassisNo LIKE %s
               OR j.MakeAndModel LIKE %s
        """
        like_pattern = f"%{search_term}%"
        # Add the pattern 5 times to the parameters list
        params.extend([like_pattern] * 5)
        
    # Order directly by the date (Removed the expensive GROUP BY)
    query += " ORDER BY j.ReceivedDate DESC"
    
    # Add a LIMIT to prevent fetching massive amounts of data at once
    if limit:
        query += " LIMIT %s"
        params.append(limit)
        
    with db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

    # Process and return the results
    return [
        {
            "No": i + 1,
            "Fullname": row[0],
            "Phone": row[1],
            "RegNo": row[2],
            "ChassisNo": row[3],
            "ReceivedDate": row[4],
            "JobCardRef": row[5],
            "MakeAndModel": row[6],
        }
        for i, row in enumerate(results)
    ]

@anvil.server.callable()
def get_car_details_and_parts(search_term, part_name):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
                SELECT 
                    tbl_clientcontacts.Fullname, 
                    tbl_clientcontacts.Phone, 
                    tbl_jobcarddetails.RegNo, 
                    tbl_jobcarddetails.ChassisNo,
                    tbl_jobcarddetails.ReceivedDate,
                    tbl_jobcarddetails.JobCardRef,
                    tbl_jobcarddetails.MakeAndModel
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
                        OR tbl_jobcarddetails.MakeAndModel LIKE %s
                    )
                    AND tbl_invoices.Item LIKE %s
                GROUP BY 
                    tbl_clientcontacts.Fullname, 
                    tbl_clientcontacts.Phone, 
                    tbl_jobcarddetails.RegNo, 
                    tbl_jobcarddetails.ChassisNo,
                    tbl_jobcarddetails.ReceivedDate,
                    tbl_jobcarddetails.JobCardRef,
                    tbl_jobcarddetails.MakeAndModel
                ORDER BY 
                    MAX(tbl_jobcarddetails.ReceivedDate) DESC
            """
        like_pattern = f"%{search_term}%"
        part_pattern = f"%{part_name}%"
        cursor.execute(
            query,
            (like_pattern, like_pattern, like_pattern, like_pattern, like_pattern, part_pattern),
        )

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
                "JobCardRef": row[5],
                "MakeAndModel": row[6],
            }
            for i, row in enumerate(results)
        ]

@anvil.server.callable
def getCarRegNoFromClientID(valueID):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT DISTINCT RegNo
            FROM tbl_jobcarddetails
            WHERE ClientDetails = %s
            ORDER BY RegNo ASC
        """
        cursor.execute(query, (valueID,))
        results = cursor.fetchall()
        
        # Return a list of registration numbers
        return [row[0] for row in results] if results else []

__all__ = [
    'getCarRegistration',
    'getCarRegistrationWithPartlyDetails',
    'get_car_details',
    'get_car_details_and_parts',
    'getCarRegNoFromClientID',
]

from . import BMALocal as _compatibility_facade
