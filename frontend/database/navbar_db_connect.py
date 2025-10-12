# utils/dbpages_connect.py
# Connection to database

"""
Database Connection Module
Handles SQLite database connections for the navigation system.

This provides basic connection functions to interact with the navbar.db database.
All database operations should use these functions to ensure consistent connection handling.
"""
import sqlite3

DB_NAME = "navbar.db"

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_NAME)

def close_connection(conn):
    """Close database connection"""
    if conn:
        conn.close()