from ._common import *

# **************************************************** Booking Details Section ************************************

@anvil.server.callable()
def saveBookingDetails(customer_id, regno, period, details):
    # Ensure the user is logged in before saving
    _get_current_user()

    with db_cursor() as cursor:
        query = """
            INSERT INTO tbl_appointmentbooking (ClientID, RegNo, Period, Details, IsSent)
            VALUES (%s, %s, %s, %s, 0)
        """
        try:
            cursor.execute(query, (customer_id, regno, period, details))
            new_id = cursor.lastrowid
        except Exception as e:
            print(f"Error saving booking: {e}")
            raise e
    invalidate_lookup_cache("upcoming_bookings")
    publish_realtime_event("bookings", "booking_created", entity_id=new_id)
    return True


@anvil.server.callable()
def getBookingDetails():
    _get_current_user()

    def _load_bookings():
        with db_cursor() as cursor:
            query = """
                SELECT
                    c.Fullname,
                    b.RegNo,
                    b.Period,
                    b.Details,
                    c.Phone,
                    b.ID
                FROM tbl_appointmentbooking b
                LEFT JOIN tbl_clientcontacts c ON b.ClientID = c.ID
                WHERE b.Period >= CURDATE() AND b.IsSent = 0
                ORDER BY b.Period ASC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

            booking_data = []
            for index, row in enumerate(rows, start=1):
                d = dict(zip(columns, row))
                dt_object = d.get("Period")
                if dt_object and hasattr(dt_object, "strftime"):
                    d["FormattedSchedule"] = dt_object.strftime("%d-%m-%Y at %I:%M %p")
                d["No"] = index
                booking_data.append(d)
            return booking_data

    return [dict(item) for item in cached_lookup("upcoming_bookings", _load_bookings, ttl_seconds=120)]


@anvil.server.callable()
def updateAppointmentSent(booking_id):
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            UPDATE tbl_appointmentbooking
            SET IsSent = 1
            WHERE ID = %s
        """
        cursor.execute(query, (booking_id,))
    invalidate_lookup_cache("upcoming_bookings")
    publish_realtime_event("bookings", "booking_sent", entity_id=booking_id)

__all__ = [
    'saveBookingDetails',
    'getBookingDetails',
    'updateAppointmentSent',
]

from . import BMALocal as _compatibility_facade
