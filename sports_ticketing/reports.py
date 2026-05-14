import logging
from db import execute_query

logger = logging.getLogger(__name__)

def get_revenue_by_event():
    """
    SELECT * FROM vw_RevenueByEvent
    Returns list of dicts with revenue data.
    Phase 1 DB object: vw_RevenueByEvent
    """
    query = "SELECT * FROM vw_RevenueByEvent"
    return execute_query(query)

def get_sold_out_events():
    """
    SELECT * FROM vw_SoldOutEvents
    Returns list of events that are sold out.
    Phase 1 DB object: vw_SoldOutEvents
    """
    query = "SELECT * FROM vw_SoldOutEvents"
    return execute_query(query)

def get_seat_availability(event_id):
    """
    SELECT * FROM vw_SeatAvailability WHERE EventID = event_id
    Phase 1 DB object: vw_SeatAvailability
    """
    query = "SELECT * FROM vw_SeatAvailability WHERE EventID = %s"
    return execute_query(query, (event_id,))

def get_total_revenue(event_id):
    """
    SELECT fn_TotalRevenue(event_id)
    Phase 1 DB object: fn_TotalRevenue
    """
    query = "SELECT fn_TotalRevenue(%s) as TotalRevenue"
    result = execute_query(query, (event_id,))
    return result[0]['TotalRevenue'] if result and result[0]['TotalRevenue'] is not None else 0

def get_tickets_sold(event_id):
    """
    SELECT fn_TicketsSold(event_id)
    Phase 1 DB object: fn_TicketsSold
    """
    query = "SELECT fn_TicketsSold(%s) as TicketsSold"
    result = execute_query(query, (event_id,))
    return result[0]['TicketsSold'] if result and result[0]['TicketsSold'] is not None else 0

def get_event_popularity():
    """
    Return top 5 events ranked by tickets sold.
    Utilizes the fn_TicketsSold UDF from Phase 1.
    """
    query = """
        SELECT EventID, EventName, EventDate, fn_TicketsSold(EventID) as TicketsSold
        FROM Events
        ORDER BY TicketsSold DESC
        LIMIT 5
    """
    return execute_query(query)
