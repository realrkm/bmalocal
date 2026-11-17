from ._common import *

# *************************************************** Get Notification Job Card Reference Section ************************************
@anvil.server.callable()
def getNotificationJobCardRef(jobCardID):
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
    
# *************************************************** Deactivate Individual Notifications Section ************************************
@anvil.server.callable()
def updateNotifications(jobcard, createdat, notification):
    _get_current_user()
    with db_cursor() as cursor:
        if notification == "InvoiceAlerts":
            query = """
                Update tbl_notifications SET active = 0 WHERE jobcard = %s AND created_at = %s
            """
        elif notification == "IncompleteDefects":
            query = """
                Update tbl_incomplete_defects SET active = 0 WHERE jobcard = %s AND created_at = %s
            """
        elif notification == "TechnicianPortal":
            query = """
                Update tbl_technician_portal_notifications SET active = 0 WHERE jobcard = %s AND created_at = %s
            """
        cursor.execute(query, (jobcard, createdat))
        

# *************************************************** Role-Based Notification Section ************************************
@anvil.server.callable()
def publish_role_notification(JobCardID, message):
    _get_current_user()
    jobcard = getNotificationJobCardRef(JobCardID)
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_notifications
            (jobcard, message, role, created_at, active)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (jobcard, message, 1, datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))), True))

@anvil.server.callable()
def fetch_role_notifications(logged_in_user):
    _get_current_user()
    if not logged_in_user:
        return []

    role_id = logged_in_user['role_id']
    notifications = []

    with db_cursor() as cursor:
        query = """
            SELECT jobcard, message, created_at
            FROM tbl_notifications
            WHERE active = 1
            ORDER BY created_at DESC
            LIMIT 1
        """
        cursor.execute(query)
        rows = cursor.fetchone()
        if rows:
            notifications.append({
                "jobcard": rows[0],
                "message": rows[1]
            })

    return notifications

@anvil.server.callable()
def fetch_active_notifications(logged_in_user):
    _get_current_user()
    if not logged_in_user:
        return []

    role_id = logged_in_user['role_id']
    notifications = []

    with db_cursor() as cursor:
        query = """
            SELECT jobcard, message, created_at, active
            FROM tbl_notifications
            WHERE active = 1 
            ORDER BY created_at DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            notifications.append({
                "jobcard": row[0],
                "message": row[1],
                "created_at": row[2].strftime("%Y-%m-%d %H:%M:%S"),
                "active": "Yes" if row[3] in (1, True) else "No"
            })

    return notifications

@anvil.server.callable()
def deactivate_notifications():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_notifications
            SET active = 0
            WHERE active = 1
        """
        cursor.execute(query,)

#  *************************************************** Incomplete Defects Notification Section ************************************
@anvil.server.callable()
def publish_defects_notification(JobCardID, message):
    _get_current_user()
    jobcard = getNotificationJobCardRef(JobCardID)
    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_incomplete_defects
            (jobcard, message, role, created_at, active)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (jobcard, message, 1, datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))), True))

@anvil.server.callable()
def fetch_active_incomplete_defects_info(logged_in_user):
    _get_current_user()
    if not logged_in_user:
        return []

    role_id = logged_in_user['role_id']
    info = []

    with db_cursor() as cursor:
        query = """
            SELECT jobcard, message, created_at, active
            FROM tbl_incomplete_defects
            WHERE active = 1
            ORDER BY created_at DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            info.append({
                "jobcard": row[0],
                "message": row[1],
                "created_at": row[2].strftime("%Y-%m-%d %H:%M:%S"),
                "active": "Yes" if row[3] in (1, True) else "No"
            })

    return info

@anvil.server.callable()
def deactivate_incomplete_defects_info():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_incomplete_defects
            SET active = 0
            WHERE active = 1
        """
        cursor.execute(query,)

# *************************************************** Main Dashboard Notifications Section ************************************
@anvil.server.callable()
def fetch_all_dashboard_notifications(logged_in_user):
    # Return empty structures if no user is logged in
    _get_current_user()
    if not logged_in_user:
        return {
            "notifications": [],
            "incomplete_defects": [],
            "technician_portal": []
        }

    role_id = logged_in_user['role_id']
    
    # Initialize the result dictionary
    result = {
        "notifications": [],
        "incomplete_defects": [],
        "technician_portal": [],
        "pricing_alert": []
    }

    # Use a single database connection for all three queries
    with db_cursor() as cursor:
        
        # 1. Fetch Role Notifications
        query_notif = """
            SELECT jobcard, message, created_at
            FROM tbl_notifications
            WHERE active = 1
            ORDER BY created_at DESC
            LIMIT 1
        """
        cursor.execute(query_notif)
        notif_row = cursor.fetchone()
        if notif_row:
            result["notifications"].append({
                "jobcard": notif_row[0],
                "message": notif_row[1]
            })

        # 2. Fetch Incomplete Defects Info
        query_defects = """
            SELECT jobcard, message, created_at, active
            FROM tbl_incomplete_defects
            WHERE active = 1
            ORDER BY created_at DESC
        """
        cursor.execute(query_defects)
        for row in cursor.fetchall():
            result["incomplete_defects"].append({
                "jobcard": row[0],
                "message": row[1],
                "created_at": row[2].strftime("%Y-%m-%d %H:%M:%S"),
                "active": "Yes" if row[3] in (1, True) else "No"
            })

        # 3. Fetch Technician Portal Info
        query_tech = """
            SELECT jobcard, message, created_at, active
            FROM tbl_technician_portal_notifications
            WHERE active = 1
            ORDER BY created_at DESC
        """
        cursor.execute(query_tech)
        for row in cursor.fetchall():
            result["technician_portal"].append({
                "jobcard": row[0],
                "message": row[1],
                "created_at": row[2].strftime("%Y-%m-%d %H:%M:%S"),
                "active": "Yes" if row[3] in (1, True) else "No"
            })
        
        # 4. Fetch Pricing Alert Details (fast existence check for badge)
        query = """
            SELECT 1
            FROM tbl_carpartnames cpn
            INNER JOIN tbl_partssellingprice psp 
                ON cpn.ID = psp.CarPartsNamesID
                AND psp.Amount > -1
            INNER JOIN (
                SELECT sp.CarPart, sp.UnitCost
                FROM tbl_stockparts sp
                INNER JOIN (
                    SELECT CarPart, MAX(ID) AS max_id
                    FROM tbl_stockparts
                    GROUP BY CarPart
                ) latest
                ON sp.CarPart = latest.CarPart 
                AND sp.ID = latest.max_id
            ) ls ON cpn.ID = ls.CarPart
            WHERE 
                ls.UnitCost IS NOT NULL
                AND psp.Amount IS NOT NULL
                AND ls.UnitCost > psp.Amount
            LIMIT 1
        """
        cursor.execute(query)
        if cursor.fetchone():
            result["pricing_alert"] = [{"has_alert": True}]

    return result

#  *************************************************** Self Service Portal - Technician Portal Notification Section ************************************
def _insert_technician_portal_notification(cursor, JobCardID, message):
    cursor.execute(
        """
        SELECT JobCardRef
        FROM tbl_jobcarddetails
        WHERE ID = %s
        """,
        (JobCardID,),
    )
    jobcard = cursor.fetchone()[0]
    query = """
        INSERT INTO tbl_technician_portal_notifications
        (jobcard, message, role, created_at, active)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(
        query,
        (
            jobcard,
            message,
            1,
            datetime.datetime.now(
                datetime.timezone(datetime.timedelta(hours=3))
            ),
            True,
        ),
    )


@anvil.server.callable()
def publish_technician_portal_notification(JobCardID, message):
    _get_current_user()
    with db_cursor() as cursor:
        _insert_technician_portal_notification(cursor, JobCardID, message)

@anvil.server.callable()
def fetch_active_technician_portal_info(logged_in_user):
    _get_current_user()
    if not logged_in_user:
        return []

    role_id = logged_in_user['role_id']
    info = []

    with db_cursor() as cursor:
        query = """
            SELECT jobcard, message, created_at, active
            FROM tbl_technician_portal_notifications
            WHERE active = 1 
            ORDER BY created_at DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            info.append({
                "jobcard": row[0],
                "message": row[1],
                "created_at": row[2].strftime("%Y-%m-%d %H:%M:%S"),
                "active": "Yes" if row[3] in (1, True) else "No"
            })

    return info

@anvil.server.callable()
def deactivate_technician_portal_info():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_technician_portal_notifications
            SET active = 0
            WHERE active = 1
        """
        cursor.execute(query,)

__all__ = [
    'getNotificationJobCardRef',
    'updateNotifications',
    'publish_role_notification',
    'fetch_role_notifications',
    'fetch_active_notifications',
    'deactivate_notifications',
    'publish_defects_notification',
    'fetch_active_incomplete_defects_info',
    'deactivate_incomplete_defects_info',
    'fetch_all_dashboard_notifications',
    '_insert_technician_portal_notification',
    'publish_technician_portal_notification',
    'fetch_active_technician_portal_info',
    'deactivate_technician_portal_info',
]

from . import BMALocal as _compatibility_facade
