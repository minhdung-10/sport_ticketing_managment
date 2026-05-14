import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import auth
import booking
import reports
from db import execute_query, execute_dml, execute_procedure

load_dotenv()

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-me-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
csrf = CSRFProtect(app)

# ==============================================================================
# GLOBAL ERROR HANDLERS
# ==============================================================================

@app.errorhandler(404)
def not_found(e):
    """Custom 404 page."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Custom 500 page."""
    logger.error("Internal server error", exc_info=True)
    return render_template('errors/500.html'), 500

# ==============================================================================
# PUBLIC ROUTES
# ==============================================================================

@app.route('/')
def index():
    """Homepage: lists all upcoming events with pagination and search."""
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('q', '').strip().lower()
        per_page = 12
        offset = (page - 1) * per_page
        
        query_conditions = []
        params = []
        
        if search_query:
            # Map English sports terms to Vietnamese keywords found in DB
            if search_query in ['football', 'bóng đá', 'soccer']:
                query_conditions.append("(LOWER(EventName) LIKE %s OR LOWER(EventName) LIKE %s OR LOWER(EventName) LIKE %s)")
                params.extend(['%fc%', '%cúp%', '%việt nam%'])
            elif search_query in ['tennis', 'quần vợt']:
                query_conditions.append("(LOWER(EventName) LIKE %s OR LOWER(EventName) LIKE %s)")
                params.extend(['%quần vợt%', '%tennis%'])
            elif search_query in ['volleyball', 'bóng chuyền']:
                query_conditions.append("(LOWER(EventName) LIKE %s OR LOWER(EventName) LIKE %s)")
                params.extend(['%bóng chuyền%', '%vtv%'])
            elif search_query in ['basketball', 'bóng rổ']:
                query_conditions.append("(LOWER(EventName) LIKE %s OR LOWER(EventName) LIKE %s)")
                params.extend(['%bóng rổ%', '%vba%'])
            else:
                # Escape SQL LIKE meta-characters so user input is treated literally
                search_escaped = (
                    search_query
                    .replace('\\', '\\\\')
                    .replace('%', '\\%')
                    .replace('_', '\\_')
                )
                query_conditions.append("(LOWER(EventName) LIKE %s OR LOWER(Venue) LIKE %s)")
                params.extend([f'%{search_escaped}%', f'%{search_escaped}%'])
                
        base_query = "SELECT * FROM Events"
        if query_conditions:
            base_query += " WHERE " + " AND ".join(query_conditions)
            
        # For total pages
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as sub"
        total = execute_query(count_query, tuple(params) if params else None)
        total_pages = (total[0]['total'] + per_page - 1) // per_page if total else 1
        
        # Actual fetch
        final_query = base_query + " ORDER BY EventDate LIMIT %s OFFSET %s"
        fetch_params = params.copy()
        fetch_params.extend([per_page, offset])
        events = execute_query(final_query, tuple(fetch_params))
        
        return render_template('index.html', events=events, page=page, total_pages=total_pages)
    except Exception as e:
        logger.error("Error loading events: %s", e, exc_info=True)
        flash(f"Error loading events: {e}", "error")
        return render_template('index.html', events=[], page=1, total_pages=1)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    """Event detail + available seats."""
    try:
        # Fetch event info
        event = execute_query("SELECT * FROM Events WHERE EventID = %s", (event_id,))
        if not event:
            flash("Event not found.", "error")
            return redirect(url_for('index'))
        
        # Fetch all seats for this event
        seats = execute_query("SELECT * FROM Seats WHERE EventID = %s", (event_id,))
        
        # Fetch ticket types for this event with remaining seats count
        tickets = execute_query(
            """SELECT t.*, 
               COUNT(s.SeatID) as Remaining
               FROM Tickets t
               LEFT JOIN Seats s ON s.EventID = t.EventID 
                 AND s.SeatType = t.TicketType
                 AND s.Status = 'available'
               WHERE t.EventID = %s
               GROUP BY t.TicketID""",
            (event_id,)
        )
        
        # Get seat availability stats
        availability_res = execute_query("SELECT * FROM vw_SeatAvailability WHERE EventID = %s", (event_id,))
        availability = availability_res[0] if availability_res else None
        
        return render_template('event.html',
            event=event[0],
            seats=seats,
            tickets=tickets,
            availability=availability
        )
    except Exception as e:
        logger.error("Error loading event %s: %s", event_id, e, exc_info=True)
        flash(f"Error loading event details: {e}", "error")
        return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User and admin login route."""
    if request.method == 'POST':
        email_or_username = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email_or_username or not password:
            flash("Email and password are required.", "error")
            return render_template('login.html')

        # Check admin credentials first
        if auth.login_admin(email_or_username, password):
            flash("Welcome, Admin!", "success")
            return redirect(url_for('admin_dashboard'))

        # Check customer credentials
        try:
            if auth.login_customer(email_or_username, password):
                flash("Logged in successfully.", "success")
                return redirect(url_for('index'))
            else:
                flash("Invalid credentials.", "error")
        except Exception as e:
            logger.error("Login error: %s", e, exc_info=True)
            flash(f"Login error: {e}", "error")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Customer registration route with server-side validation."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '')

        # --- Server-side validation ---
        errors = []
        if not name or len(name) < 2:
            errors.append("Name must be at least 2 characters.")
        if not email or '@' not in email:
            errors.append("A valid email address is required.")
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters.")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template('register.html')

        success, message = auth.register_customer(name, email, phone, address, password)
        if success:
            flash(message, "success")
            return redirect(url_for('login'))
        else:
            flash(message, "error")

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout current user or admin."""
    auth.logout()
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

# ==============================================================================
# CUSTOMER ROUTES (Require Login)
# ==============================================================================

@app.route('/auto_checkout/<int:event_id>/<int:ticket_id>', methods=['POST'])
@auth.require_login
def auto_checkout(event_id, ticket_id):
    """Automatically find available seats for the selected ticket type and proceed to checkout."""
    qty_str = request.form.get('qty', 1)
    try:
        qty = int(qty_str)
    except ValueError:
        qty = 1
        
    if qty < 1 or qty > 4:
        flash("You can only buy between 1 and 4 tickets at a time.", "error")
        return redirect(url_for('event_detail', event_id=event_id))

    # First, get the TicketType
    ticket_query = "SELECT TicketType FROM Tickets WHERE TicketID = %s"
    ticket = execute_query(ticket_query, (ticket_id,))
    if not ticket:
        flash("Invalid ticket selection.", "error")
        return redirect(url_for('event_detail', event_id=event_id))
    
    ticket_type = ticket[0]['TicketType']
    
    # Find available seats
    seat_query = """
        SELECT SeatID FROM Seats 
        WHERE EventID = %s AND SeatType = %s AND Status = 'Available' 
        LIMIT %s
    """
    seats = execute_query(seat_query, (event_id, ticket_type, qty))
    
    if not seats or len(seats) < qty:
        flash(f"Sorry, only {len(seats)} {ticket_type} seats are available for this event.", "error")
        return redirect(url_for('event_detail', event_id=event_id))

    # Reserve each seat (10-minute hold); sp_ReserveSeat handles race conditions via FOR UPDATE
    reserved_ids = []
    for seat in seats:
        if execute_procedure('sp_ReserveSeat', (seat['SeatID'],)):
            reserved_ids.append(str(seat['SeatID']))
        else:
            flash("A seat could not be reserved. Please try again.", "error")
            return redirect(url_for('event_detail', event_id=event_id))

    seat_ids = ",".join(reserved_ids)
    return redirect(url_for('checkout', seat_ids=seat_ids, ticket_id=ticket_id))

@app.route('/checkout/<string:seat_ids>/<int:ticket_id>')
@auth.require_login
def checkout(seat_ids, ticket_id):
    """Booking summary before confirmation."""
    try:
        seat_id_list = [int(sid) for sid in seat_ids.split(',')]
        if not seat_id_list:
            flash("No seats selected.", "error")
            return redirect(url_for('index'))

        seats = []
        for sid in seat_id_list:
            seat = booking.get_seat_detail(sid)
            if not seat or seat['Status'] != 'reserved':
                flash("Sorry, one or more seat reservations are no longer valid.", "error")
                return redirect(url_for('event_detail', event_id=seat['EventID'] if seat else 0))
            seats.append(seat)

        ticket = execute_query("SELECT * FROM Tickets WHERE TicketID = %s", (ticket_id,))
        if not ticket:
            flash("Ticket not found.", "error")
            return redirect(url_for('index'))

        total_price = ticket[0]['Price'] * len(seats)

        return render_template('checkout.html', seats=seats, ticket=ticket[0], total_price=total_price, seat_ids=seat_ids)
    except Exception as e:
        logger.error("Error loading checkout: %s", e, exc_info=True)
        flash(f"Error loading checkout: {e}", "error")
        return redirect(url_for('index'))

@app.route('/confirm-booking', methods=['POST'])
@auth.require_login
def confirm_booking():
    """Confirms a booking by calling the database stored procedure."""
    # --- Validate and cast form inputs ---
    try:
        seat_ids_str = request.form.get('seat_ids')
        ticket_id = int(request.form.get('ticket_id'))
        seat_id_list = [int(sid) for sid in seat_ids_str.split(',')]
    except (TypeError, ValueError):
        flash("Invalid booking data.", "error")
        return redirect(url_for('index'))

    customer_id = session.get('CustomerID')

    try:
        success_count = 0
        for seat_id in seat_id_list:
            success, message = booking.book_ticket(customer_id, seat_id, ticket_id)
            if success:
                success_count += 1

        if success_count == len(seat_id_list):
            flash(f"Successfully booked {success_count} tickets!", "success")
            return redirect(url_for('my_tickets'))
        elif success_count > 0:
            flash(f"Partially successful: {success_count} out of {len(seat_id_list)} tickets booked.", "warning")
            return redirect(url_for('my_tickets'))
        else:
            flash("Sorry, seats were just taken or booking failed.", "error")
            return redirect(url_for('index'))
    except Exception as e:
        logger.error("Error during booking: %s", e, exc_info=True)
        flash(f"Error during booking: {e}", "error")
        return redirect(url_for('index'))

@app.route('/my-tickets')
@auth.require_login
def my_tickets():
    """Displays the customer's booking history."""
    try:
        customer_id = session.get('CustomerID')
        bookings = booking.get_customer_bookings(customer_id)
        return render_template('my_tickets.html', bookings=bookings)
    except Exception as e:
        logger.error("Error loading tickets: %s", e, exc_info=True)
        flash(f"Error loading your tickets: {e}", "error")
        return render_template('my_tickets.html', bookings=[])

@app.route('/cancel/<int:booking_id>', methods=['POST'])
@auth.require_login
def cancel(booking_id):
    """Cancels a specific booking after verifying ownership."""
    try:
        # --- IDOR protection: verify the booking belongs to the logged-in user ---
        customer_id = session.get('CustomerID')
        booking_check = execute_query(
            "SELECT CustomerID FROM Bookings WHERE BookingID = %s",
            (booking_id,)
        )
        if not booking_check or booking_check[0]['CustomerID'] != customer_id:
            flash("Unauthorized: this booking does not belong to you.", "error")
            return redirect(url_for('my_tickets'))

        success, message = booking.cancel_booking(booking_id)
        if success:
            flash("Booking cancelled successfully.", "success")
        else:
            flash("Booking not found.", "error")
    except Exception as e:
        logger.error("Error cancelling booking %s: %s", booking_id, e, exc_info=True)
        flash(f"Error cancelling booking: {e}", "error")

    return redirect(url_for('my_tickets'))

@app.route('/sell', methods=['GET', 'POST'])
@auth.require_login
def sell_ticket():
    """Route for users to resell their tickets."""
    if request.method == 'POST':
        try:
            booking_id = int(request.form.get('booking_id', 0))
            asking_price = float(request.form.get('asking_price', 0))
        except (TypeError, ValueError):
            flash("Invalid booking or price value.", "error")
            return redirect(url_for('sell_ticket'))

        if asking_price <= 0:
            flash("Asking price must be greater than zero.", "error")
            return redirect(url_for('sell_ticket'))

        try:
            customer_id = session.get('CustomerID')
            booking_row = execute_query(
                "SELECT * FROM Bookings WHERE BookingID = %s AND CustomerID = %s",
                (booking_id, customer_id)
            )
            if not booking_row:
                flash("Invalid booking or unauthorized.", "error")
                return redirect(url_for('sell_ticket'))

            rows = execute_dml(
                "INSERT INTO ResellListings (BookingID, SellerID, AskingPrice) VALUES (%s, %s, %s)",
                (booking_id, customer_id, asking_price)
            )
            if rows < 0:
                flash("Error listing ticket for resale.", "error")
            else:
                flash("Ticket listed for resale successfully!", "success")
                return redirect(url_for('my_tickets'))
        except Exception as e:
            logger.error("Error listing ticket: %s", e)
            flash("Error listing ticket for resale.", "error")
            
    customer_id = session.get('CustomerID')
    bookings = execute_query("""
        SELECT b.BookingID, e.EventName, s.SeatNumber, s.SeatType
        FROM Bookings b
        JOIN Seats s ON b.SeatID = s.SeatID
        JOIN Events e ON s.EventID = e.EventID
        WHERE b.CustomerID = %s AND b.Status = 'confirmed'
          AND b.BookingID NOT IN (SELECT BookingID FROM ResellListings WHERE Status = 'active')
    """, (customer_id,))
    
    return render_template('sell.html', bookings=bookings)



# ==============================================================================
# ADMIN ROUTES (Require Admin Role)
# ==============================================================================

@app.route('/admin')
@auth.require_admin
def admin_dashboard():
    """Admin dashboard overview."""
    try:
        popularity = reports.get_event_popularity()
        revenue_data = reports.get_revenue_by_event()
        
        # Calculate summary metrics
        total_revenue = sum([float(r['TotalRevenue'] or 0) for r in revenue_data])
        total_tickets_sold = sum([int(r['TicketsSold'] or 0) for r in revenue_data])
        
        # Count active events
        active_events = execute_query("SELECT COUNT(*) as count FROM Events WHERE EventDate >= CURDATE()")
        active_events_count = active_events[0]['count'] if active_events else 0
        
        # Count total bookings
        bookings_count_q = execute_query("SELECT COUNT(*) as count FROM Bookings")
        total_bookings = bookings_count_q[0]['count'] if bookings_count_q else 0
        
        # Sales over time
        sales_time = execute_query("SELECT DATE_FORMAT(BookingDate, '%%b %%d') as Date, COUNT(*) as count FROM Bookings WHERE Status = 'confirmed' GROUP BY DATE(BookingDate) ORDER BY DATE(BookingDate) DESC LIMIT 7")
        sales_time_dates = [row['Date'] for row in reversed(sales_time)] if sales_time else []
        sales_time_counts = [row['count'] for row in reversed(sales_time)] if sales_time else []
        
        # Sales by ticket type
        ticket_types = execute_query("SELECT s.SeatType, COUNT(*) as count FROM Bookings b JOIN Seats s ON b.SeatID = s.SeatID WHERE b.Status = 'confirmed' GROUP BY s.SeatType")
        ticket_type_labels = [row['SeatType'] for row in ticket_types] if ticket_types else []
        ticket_type_counts = [row['count'] for row in ticket_types] if ticket_types else []
        
        return render_template('admin/dashboard.html', 
                               top_events=popularity,
                               total_revenue=total_revenue,
                               total_tickets_sold=total_tickets_sold,
                               active_events_count=active_events_count,
                               total_bookings=total_bookings,
                               sales_time_dates=sales_time_dates,
                               sales_time_counts=sales_time_counts,
                               ticket_type_labels=ticket_type_labels,
                               ticket_type_counts=ticket_type_counts,
                               revenue_data=revenue_data)
    except Exception as e:
        logger.error("Error loading dashboard: %s", e, exc_info=True)
        flash(f"Error loading dashboard data: {e}", "error")
        return render_template('admin/dashboard.html', top_events=[], total_revenue=0, total_tickets_sold=0, active_events_count=0, total_bookings=0)

@app.route('/admin/reports')
@auth.require_admin
def admin_reports():
    """Detailed revenue reports for admins."""
    try:
        revenue_data = reports.get_revenue_by_event()
        sold_out = reports.get_sold_out_events()
        return render_template('admin/reports.html', revenue=revenue_data, sold_out=sold_out)
    except Exception as e:
        logger.error("Error loading reports: %s", e, exc_info=True)
        flash(f"Error loading report data: {e}", "error")
        return render_template('admin/reports.html', revenue=[], sold_out=[])

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')
