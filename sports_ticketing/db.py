import os
import logging
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection Pool
# ---------------------------------------------------------------------------
_pool = None

def _get_pool():
    """Lazily initializes and returns the connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="ticketing_pool",
                pool_size=5,
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'sportsticketingdb'),
                user=os.getenv('DB_USER', 'admin_user'),
                password=os.getenv('DB_PASSWORD', '')
            )
            logger.info("Database connection pool created successfully.")
        except Error as e:
            logger.error("Failed to create connection pool: %s", e)
            return None
    return _pool

def get_connection():
    """
    Returns a MySQL connection from the pool.
    Falls back to a direct connection if the pool is unavailable.
    """
    pool = _get_pool()
    if pool:
        try:
            return pool.get_connection()
        except Error as e:
            logger.warning("Pool exhausted, creating direct connection: %s", e)

    # Fallback: direct connection
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'sportsticketingdb'),
            user=os.getenv('DB_USER', 'admin_user'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return connection
    except Error as e:
        logger.error("Error connecting to MySQL: %s", e)
        return None

# ---------------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------------

def execute_query(query, params=None):
    """
    Executes a SELECT query and returns a list of dictionaries.
    Uses dictionary=True cursor.
    """
    connection = get_connection()
    if not connection:
        return []

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
    except Error as e:
        logger.error("Error executing query: %s | params=%s", query, params, exc_info=True)
        return []
    finally:
        if connection and connection.is_connected():
            connection.close()

def execute_procedure(proc_name, args):
    """
    Calls stored procedures (e.g. sp_BookTicket, sp_CancelBooking) and commits.
    Returns True if successful, False otherwise.
    """
    connection = get_connection()
    if not connection:
        return False

    try:
        with connection.cursor() as cursor:
            cursor.callproc(proc_name, args)
            connection.commit()
            return True
    except Error as e:
        logger.error("Error executing procedure %s: %s", proc_name, e, exc_info=True)
        if connection and connection.is_connected():
            connection.rollback()
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()
