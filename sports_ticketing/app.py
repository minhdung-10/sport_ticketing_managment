import os
import logging
import stripe
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import auth
import booking
import reports
from db import execute_query, execute_procedure

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

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# ==============================================================================
# RESPONSE HEADERS
# ==============================================================================

@app.after_request
def add_no_cache_headers(response):
    """Prevent the browser from serving stale HTML during development."""
    if response.mimetype == 'text/html':
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

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
    """Event detail page with ticket types and live seat availability."""
    try:
        event = execute_query("SELECT * FROM Events WHERE EventID = %s", (event_id,))
        if not event:
            flash("Event not found.", "error")
            return redirect(url_for('index'))

        # Ticket types for this event with a live count of available seats
        tickets = execute_query(
            """SELECT t.*,
               COUNT(s.SeatID) as Remaining
               FROM Tickets t
               LEFT JOIN Seats s ON s.EventID = t.EventID
                 AND s.SeatType = t.TicketType
                 AND s.Status = 'available'
               WHERE t.EventID = %s
               GROUP BY t.TicketID
               ORDER BY t.Price DESC""",
            (event_id,)
        )

        return render_template('event.html', event=event[0], tickets=tickets)
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
        if not phone or len(phone) < 8:
            errors.append("A valid phone number is required.")
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
        WHERE EventID = %s AND SeatType = %s AND Status = 'available' 
        LIMIT %s
    """
    seats = execute_query(seat_query, (event_id, ticket_type, qty))
    
    if not seats or len(seats) < qty:
        flash(f"Sorry, only {len(seats)} {ticket_type} seats are available for this event.", "error")
        return redirect(url_for('event_detail', event_id=event_id))

    # Reserve each seat (10-minute hold); sp_ReserveSeat handles race conditions via FOR UPDATE
    reserved_ids = []
    for seat in seats:
        success, err = execute_procedure('sp_ReserveSeat', (seat['SeatID'],))
        if success:
            reserved_ids.append(str(seat['SeatID']))
        else:
            flash(f"A seat could not be reserved: {err}", "error")
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

        return render_template('checkout.html', seats=seats, ticket=ticket[0], total_price=total_price, seat_ids=seat_ids, stripe_public_key=os.getenv('STRIPE_PUBLIC_KEY'))
    except Exception as e:
        logger.error("Error loading checkout: %s", e, exc_info=True)
        flash(f"Error loading checkout: {e}", "error")
        return redirect(url_for('index'))

@app.route('/create-checkout-session', methods=['POST'])
@auth.require_login
def create_checkout_session():
    """Creates a Stripe Checkout session and redirects the user."""
    try:
        seat_ids_str = request.form.get('seat_ids')
        ticket_id = int(request.form.get('ticket_id'))
        seat_id_list = [int(sid) for sid in seat_ids_str.split(',')]
    except (TypeError, ValueError):
        flash("Invalid booking data.", "error")
        return redirect(url_for('index'))

    # Fetch ticket details
    ticket = execute_query("SELECT * FROM Tickets WHERE TicketID = %s", (ticket_id,))
    if not ticket:
        flash("Ticket not found.", "error")
        return redirect(url_for('index'))
    
    price = float(ticket[0]['Price'])
    ticket_name = f"{ticket[0]['TicketType']} Ticket"
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'vnd',
                        'unit_amount': int(price), # VND is a zero-decimal currency
                        'product_data': {
                            'name': ticket_name,
                        },
                    },
                    'quantity': len(seat_id_list),
                },
            ],
            mode='payment',
            success_url=url_for('booking_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('booking_cancel', _external=True),
            metadata={
                'seat_ids': seat_ids_str,
                'ticket_id': ticket_id,
                'customer_id': session.get('CustomerID')
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        logger.error("Error creating checkout session: %s", e, exc_info=True)
        flash(f"Payment error: {e}", "error")
        return redirect(url_for('index'))

@app.route('/booking-success')
@auth.require_login
def booking_success():
    """Handles successful Stripe payment and commits the booking."""
    session_id = request.args.get('session_id')
    if not session_id:
        flash("Invalid session.", "error")
        return redirect(url_for('index'))
    
    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        if checkout_session.payment_status != 'paid':
            flash("Payment not completed.", "error")
            return redirect(url_for('index'))

        metadata = checkout_session.to_dict().get('metadata', {})
        seat_ids_str = metadata.get('seat_ids')
        ticket_id = int(metadata.get('ticket_id'))
        customer_id = int(metadata.get('customer_id'))

        if customer_id != session.get('CustomerID'):
            flash("Unauthorized transaction.", "error")
            return redirect(url_for('index'))

        seat_id_list = [int(sid) for sid in seat_ids_str.split(',')]

        success_count = 0
        for seat_id in seat_id_list:
            success, message = booking.book_ticket(customer_id, seat_id, ticket_id)
            if success:
                success_count += 1

        if success_count == len(seat_id_list):
            flash(f"Payment successful! Successfully booked {success_count} tickets.", "success")
        elif success_count > 0:
            flash(f"Payment successful, but partially fulfilled: {success_count} out of {len(seat_id_list)} tickets booked.", "warning")
        else:
            flash("Payment successful, but seats were taken or booking failed. Please contact support.", "error")
            
        return redirect(url_for('my_tickets'))
        
    except Exception as e:
        logger.error("Error finalizing booking: %s", e, exc_info=True)
        flash(f"Error finalizing booking: {e}", "error")
        return redirect(url_for('index'))

@app.route('/booking-cancel')
@auth.require_login
def booking_cancel():
    """Handles cancelled Stripe payment."""
    flash("Payment cancelled. Your seat reservations may expire soon.", "warning")
    return redirect(url_for('index'))

@app.route('/stripe-webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    """Listens for Stripe webhook events to reliably fulfill orders."""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    if not endpoint_secret:
        return 'Webhook secret not configured.', 400

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object'].to_dict()
        
        metadata = session_obj.get('metadata', {})
        seat_ids_str = metadata.get('seat_ids')
        ticket_id = metadata.get('ticket_id')
        customer_id = metadata.get('customer_id')
        
        if seat_ids_str and ticket_id and customer_id:
            seat_id_list = [int(sid) for sid in seat_ids_str.split(',')]
            for seat_id in seat_id_list:
                # Attempt to book the ticket. 
                # If already booked by the success_url, this will safely fail/ignore.
                try:
                    booking.book_ticket(int(customer_id), seat_id, int(ticket_id))
                except Exception as e:
                    logger.error(f"Webhook booking error: {e}")
                
    return '', 200

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
        total_tickets_sold = sum([int(r['TotalTicketsSold'] or 0) for r in revenue_data])
        
        # Count active events
        active_events = execute_query("SELECT COUNT(*) as count FROM Events WHERE EventDate >= CURDATE()")
        active_events_count = active_events[0]['count'] if active_events else 0
        
        # Count total bookings
        bookings_count_q = execute_query("SELECT COUNT(*) as count FROM Bookings")
        total_bookings = bookings_count_q[0]['count'] if bookings_count_q else 0
        
        # Sales over time (last 7 days)
        sales_time = execute_query("""
            SELECT DATE_FORMAT(BookingDate, '%%b %%d') as Date, COUNT(*) as count
            FROM Bookings
            WHERE Status = 'confirmed'
            GROUP BY DATE(BookingDate)
            ORDER BY DATE(BookingDate) DESC
            LIMIT 7
        """)
        sales_time_dates = [row['Date'] for row in reversed(sales_time)] if sales_time else []
        sales_time_counts = [row['count'] for row in reversed(sales_time)] if sales_time else []

        # Sales over time (last 12 months)
        sales_month = execute_query("""
            SELECT DATE_FORMAT(BookingDate, '%%b %%Y') as Period, COUNT(*) as count
            FROM Bookings
            WHERE Status = 'confirmed'
            GROUP BY DATE_FORMAT(BookingDate, '%%Y-%%m')
            ORDER BY DATE_FORMAT(BookingDate, '%%Y-%%m') DESC
            LIMIT 12
        """)
        sales_month_dates = [row['Period'] for row in reversed(sales_month)] if sales_month else []
        sales_month_counts = [row['count'] for row in reversed(sales_month)] if sales_month else []

        # Sales over time (by year)
        sales_year = execute_query("""
            SELECT YEAR(BookingDate) as Period, COUNT(*) as count
            FROM Bookings
            WHERE Status = 'confirmed'
            GROUP BY YEAR(BookingDate)
            ORDER BY YEAR(BookingDate)
        """)
        sales_year_dates = [str(row['Period']) for row in sales_year] if sales_year else []
        sales_year_counts = [row['count'] for row in sales_year] if sales_year else []
        
        # Sales by ticket type
        ticket_types = execute_query("SELECT s.SeatType, COUNT(*) as count FROM Bookings b JOIN Seats s ON b.SeatID = s.SeatID WHERE b.Status = 'confirmed' GROUP BY s.SeatType")
        ticket_type_labels = [row['SeatType'] for row in ticket_types] if ticket_types else []
        ticket_type_counts = [row['count'] for row in ticket_types] if ticket_types else []

        # Per-event breakdown built from the Phase 1 UDFs (fn_TicketsSold,
        # fn_TotalRevenue) and the vw_SeatAvailability view.
        all_events = execute_query("SELECT EventID, EventName FROM Events ORDER BY EventDate")
        event_breakdown = []
        for ev in all_events:
            eid = ev['EventID']
            availability = reports.get_seat_availability(eid)
            seats = availability[0] if availability else {}
            event_breakdown.append({
                'EventID': eid,
                'EventName': ev['EventName'],
                'TicketsSold': reports.get_tickets_sold(eid),
                'Revenue': reports.get_total_revenue(eid),
                'TotalSeats': seats.get('TotalSeats', 0),
                'BookedSeats': seats.get('BookedSeats', 0),
                'AvailableSeats': seats.get('AvailableSeats', 0),
            })

        return render_template('admin/dashboard.html',
                               top_events=popularity,
                               total_revenue=total_revenue,
                               total_tickets_sold=total_tickets_sold,
                               active_events_count=active_events_count,
                               total_bookings=total_bookings,
                               sales_time_dates=sales_time_dates,
                               sales_time_counts=sales_time_counts,
                               sales_month_dates=sales_month_dates,
                               sales_month_counts=sales_month_counts,
                               sales_year_dates=sales_year_dates,
                               sales_year_counts=sales_year_counts,
                               ticket_type_labels=ticket_type_labels,
                               ticket_type_counts=ticket_type_counts,
                               event_breakdown=event_breakdown,
                               revenue_data=revenue_data)
    except Exception as e:
        logger.error("Error loading dashboard: %s", e, exc_info=True)
        flash(f"Error loading dashboard data: {e}", "error")
        return render_template('admin/dashboard.html', top_events=[], total_revenue=0, total_tickets_sold=0, active_events_count=0, total_bookings=0, event_breakdown=[])

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
