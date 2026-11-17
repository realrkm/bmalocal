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
            # If your connection doesn't auto-commit, uncomment the next line:
            # cursor.connection.commit()
            return True
        except Exception as e:
            # Log the error and raise it back to the UI if needed
            print(f"Error saving booking: {e}")
            raise e
        
@anvil.server.callable()
def getBookingDetails():
    _get_current_user()
    with db_cursor() as cursor:
        query = """
            SELECT 
                c.Fullname, 
                b.RegNo, 
                b.Period, 
                b.Details,
                c.Phone,
                b.RegNo,
                b.ID
            FROM tbl_appointmentbooking b
            LEFT JOIN tbl_clientcontacts c ON b.ClientID = c.ID
            WHERE DATE(b.Period) >= CURDATE() AND b.IsSent = 0
            ORDER BY b.Period 
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        columns = [col[0] for col in cursor.description]
        
        booking_data = []
        for index, row in enumerate(rows, start=1):
            d = dict(zip(columns, row))
            
            dt_object = d['Period']
            
            if dt_object:
                # Combined format: "27-04-2026 at 11:00 AM"
                d['FormattedSchedule'] = dt_object.strftime("%d-%m-%Y at %I:%M %p")
            
            d['No'] = index
            booking_data.append(d)
            
        return booking_data

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

__all__ = [
    'saveBookingDetails',
    'getBookingDetails',
    'updateAppointmentSent',
]

from . import BMALocal as _compatibility_facade
