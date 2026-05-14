events = {
    1: [('VIP', 10), ('Standard', 20), ('Economy', 10)],
    2: [('VIP', 10), ('Standard', 30)],
    3: [('Standard', 40)],
    4: [('VIP', 20), ('Economy', 20)],
    5: [('VIP', 10), ('Standard', 20), ('Economy', 10)]
}

out = []
for ev, types in events.items():
    for t_name, count in types:
        prefix = t_name[0]
        # if booked we need to skip? No, we will make everything available,
        # but to keep the Bookings working we should probably preserve the first few seats.
        # Wait, if we replace the Seats table completely, we'll break the Bookings table 
        # unless we ensure the IDs match! Seat 1, 3, 5, 6 are booked.
        # Actually, let's just make ALL of them available. 
        # Wait, Bookings references SeatID 1, 3, 5, 6. If we insert 40 seats each, SeatIDs will be sequentially 1 to 200.
        # So Seat 1 is Event 1 VIP. Seat 3 is Event 1 VIP. Seat 5 is Event 1 VIP. Seat 6 is Event 1 VIP.
        # But Bookings says:
        # Booking 1: Seat 1, Ticket 1 (Event 1 VIP)
        # Booking 2: Seat 3, Ticket 2 (Event 1 Standard) -> But if Seat 3 is VIP, the ticket type won't match our new IDOR check!
        # Ah! I need to manually set the first few seats to match exactly what is in Bookings.
        pass

# Bookings:
# (1, 1, 1, 'confirmed') -> Seat 1 is Event 1, Ticket 1 (VIP)
# (2, 3, 2, 'confirmed') -> Seat 3 is Event 1, Ticket 2 (Standard)
# (3, 5, 4, 'confirmed') -> Seat 5 is Event 2, Ticket 4 (VIP)
# (4, 6, 5, 'confirmed') -> Seat 6 is Event 2, Ticket 5 (Standard)

# Let's generate exactly:
seats = []
seats.append("(1, 'V1', 'VIP', 'booked')")      # ID 1
seats.append("(1, 'V2', 'VIP', 'available')")    # ID 2
seats.append("(1, 'S1', 'Standard', 'booked')")  # ID 3
seats.append("(1, 'E1', 'Economy', 'available')")# ID 4
seats.append("(2, 'V1', 'VIP', 'booked')")      # ID 5
seats.append("(2, 'S1', 'Standard', 'booked')")  # ID 6

# Now let's add 40 seats for each event starting from index 2 to avoid collisions.
# Actually, Event 1 already has 4 seats. Let's add 36 more for Event 1.
# Event 2 has 2 seats. Let's add 38 more.
# Event 3, 4, 5 get 40 each.

for i in range(3, 13): seats.append(f"(1, 'V{i}', 'VIP', 'available')")
for i in range(2, 18): seats.append(f"(1, 'S{i}', 'Standard', 'available')")
for i in range(2, 12): seats.append(f"(1, 'E{i}', 'Economy', 'available')")

for i in range(2, 12): seats.append(f"(2, 'V{i}', 'VIP', 'available')")
for i in range(2, 30): seats.append(f"(2, 'S{i}', 'Standard', 'available')")

for i in range(1, 41): seats.append(f"(3, 'S{i}', 'Standard', 'available')")

for i in range(1, 21): seats.append(f"(4, 'V{i}', 'VIP', 'available')")
for i in range(1, 21): seats.append(f"(4, 'E{i}', 'Economy', 'available')")

for i in range(1, 11): seats.append(f"(5, 'V{i}', 'VIP', 'available')")
for i in range(1, 21): seats.append(f"(5, 'S{i}', 'Standard', 'available')")
for i in range(1, 11): seats.append(f"(5, 'E{i}', 'Economy', 'available')")

with open('seats_sql.txt', 'w', encoding='utf-8') as f:
    f.write('INSERT INTO Seats (EventID, SeatNumber, SeatType, Status) VALUES\n')
    f.write(',\n'.join(seats))
    f.write(';\n')
