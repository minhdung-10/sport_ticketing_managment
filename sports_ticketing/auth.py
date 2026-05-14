import os
import logging
from functools import wraps
from flask import session, redirect, url_for, flash
import bcrypt
from db import execute_query, get_connection
from mysql.connector import Error

logger = logging.getLogger(__name__)

def register_customer(name, email, phone, address, password):
    """
    Registers a new customer.
    Hashes password with bcrypt before INSERT into Customers.
    Returns (success_boolean, message_string).
    """
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    connection = get_connection()
    if not connection:
        return False, "Database connection failed"

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO Customers (CustomerName, Email, PhoneNumber, Address, PasswordHash)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, phone, address, hashed_password))
        connection.commit()
        return True, "Registration successful"
    except Error as e:
        if connection.is_connected():
            connection.rollback()
        if "Duplicate entry" in str(e) or "1062" in str(e):
            return False, "Email already exists"
        logger.error("Registration failed: %s", e, exc_info=True)
        return False, f"Registration failed: {e}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def login_customer(email, password):
    """
    Fetches customer by email, verifies bcrypt hash, and stores session data.
    """
    query = "SELECT CustomerID, CustomerName, PasswordHash FROM Customers WHERE Email = %s"
    result = execute_query(query, (email,))

    if result:
        customer = result[0]
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), customer['PasswordHash'].encode('utf-8')):
            session['CustomerID'] = customer['CustomerID']
            session['CustomerName'] = customer['CustomerName']
            session['role'] = 'customer'
            return True
    return False

def login_admin(username, password):
    """
    Admin login with bcrypt-hashed password stored in environment variable.
    """
    admin_user = os.getenv('ADMIN_USERNAME', 'admin')
    admin_hash = os.getenv('ADMIN_PASSWORD_HASH')

    if not admin_hash:
        logger.warning("ADMIN_PASSWORD_HASH not set in environment.")
        return False

    if username == admin_user:
        try:
            if bcrypt.checkpw(password.encode('utf-8'), admin_hash.encode('utf-8')):
                session['role'] = 'admin'
                return True
        except Exception as e:
            logger.error("Admin login bcrypt error: %s", e)
            return False
    return False

def is_logged_in():
    """Returns True if session has CustomerID"""
    return 'CustomerID' in session

def is_admin():
    """Returns True if session role == 'admin'"""
    return session.get('role') == 'admin'

def logout():
    """Clears session"""
    session.clear()

def require_login(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash("Admin access required.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
