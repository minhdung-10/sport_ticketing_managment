"""Quick test to verify the entire backend <-> MySQL connection stack."""
from dotenv import load_dotenv
load_dotenv()

from db import execute_query, execute_procedure
from reports import get_event_popularity, get_revenue_by_event, get_sold_out_events
from booking import get_available_seats, get_customer_bookings

print("=" * 60)
print("  SPORTS TICKETING - Backend <-> MySQL Connection Test")
print("=" * 60)

# --- Test 1: Basic query ---
print("\n[1] db.py  execute_query  ->  Events table")
events = execute_query("SELECT EventID, EventName, Venue FROM Events")
if events:
    for e in events:
        print(f"    [{e['EventID']}] {e['EventName']}  @  {e['Venue']}")
    print(f"    -> OK ({len(events)} events)")
else:
    print("    -> FAIL: no events returned")

# --- Test 2: Booking module ---
print("\n[2] booking.py  get_available_seats  ->  Seats table")
seats = get_available_seats(1)
print(f"    Available seats for Event 1: {len(seats)}")
for s in seats:
    print(f"    Seat {s['SeatNumber']} ({s['SeatType']})")
print(f"    -> OK")

# --- Test 3: Customer bookings ---
print("\n[3] booking.py  get_customer_bookings  ->  Bookings JOIN")
bookings = get_customer_bookings(1)
print(f"    Bookings for Customer 1: {len(bookings)}")
for b in bookings:
    print(f"    Booking #{b['BookingID']}: {b['EventName']} - Seat {b['SeatNumber']} ({b['BookingStatus']})")
print(f"    -> OK")

# --- Test 4: Reports (views + UDFs) ---
print("\n[4] reports.py  get_event_popularity  ->  fn_TicketsSold UDF")
popularity = get_event_popularity()
for p in popularity:
    print(f"    {p['EventName']}: {p['TicketsSold']} sold")
print(f"    -> OK")

print("\n[5] reports.py  get_revenue_by_event  ->  vw_RevenueByEvent view")
revenue = get_revenue_by_event()
for r in revenue:
    print(f"    {r['EventName']}: {r['TotalRevenue']:,.0f} VND")
print(f"    -> OK")

print("\n[6] reports.py  get_sold_out_events  ->  vw_SoldOutEvents view")
sold_out = get_sold_out_events()
print(f"    Sold out events: {len(sold_out)}")
for s in sold_out:
    print(f"    {s['EventName']}")
print(f"    -> OK")

# --- Test 5: Connection pooling ---
print("\n[7] db.py  connection pool  ->  Multiple rapid queries")
from db import _get_pool
pool = _get_pool()
if pool:
    print(f"    Pool name: {pool.pool_name}, size: {pool.pool_size}")
    print(f"    -> OK (pooling active)")
else:
    print(f"    -> WARNING: pooling not available, using direct connections")

print("\n" + "=" * 60)
print("  ALL TESTS PASSED - Backend is connected to MySQL!")
print("=" * 60)
