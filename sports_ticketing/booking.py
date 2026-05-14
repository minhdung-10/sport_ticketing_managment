from db import execute_query, execute_procedure

def get_available_seats(event_id):
    """
    Query Seats WHERE EventID = event_id AND Status = 'available'
    Returns list of seat dicts.
    """
    query = """
        SELECT SeatID, SeatNumber, SeatType, Status, EventID
        FROM Seats
        WHERE EventID = %s AND Status = 'available'
    """
    return execute_query(query, (event_id,))

def book_ticket(customer_id, seat_id, ticket_id):
    """
    Calls stored procedure sp_BookTicket via execute_procedure().
    Returns (success_boolean, message_string).
    """
    # Phase 1 DB object: sp_BookTicket
    success, err = execute_procedure('sp_BookTicket', (customer_id, seat_id, ticket_id))
    if success:
        return True, "Booking successful"
    else:
        return False, f"Booking failed: {err}"

def cancel_booking(booking_id):
    """
    Calls stored procedure sp_CancelBooking via execute_procedure().
    Returns (success_boolean, message_string).
    """
    # Phase 1 DB object: sp_CancelBooking
    success, err = execute_procedure('sp_CancelBooking', (booking_id,))
    if success:
        return True, "Cancellation successful"
    else:
        return False, f"Cancellation failed: {err}"

def get_customer_bookings(customer_id):
    """
    Query Bookings JOIN Seats JOIN Events JOIN Tickets
    WHERE CustomerID = customer_id.
    Returns full booking history with event name, seat, ticket type, price.
    """
    query = """
        SELECT b.BookingID, b.BookingDate, b.Status as BookingStatus,
               s.SeatNumber, s.SeatType,
               e.EventName, e.EventDate,
               t.TicketType, t.Price
        FROM Bookings b
        JOIN Seats s ON b.SeatID = s.SeatID
        JOIN Events e ON s.EventID = e.EventID
        JOIN Tickets t ON b.TicketID = t.TicketID
        WHERE b.CustomerID = %s
        ORDER BY b.BookingDate DESC
    """
    return execute_query(query, (customer_id,))

def get_seat_detail(seat_id):
    """
    Returns single seat info (SeatNumber, SeatType, Status, EventID).
    """
    query = """
        SELECT SeatID, SeatNumber, SeatType, Status, EventID
        FROM Seats
        WHERE SeatID = %s
    """
    result = execute_query(query, (seat_id,))
    return result[0] if result else None
