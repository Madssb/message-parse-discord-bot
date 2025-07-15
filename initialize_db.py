# initialize_db.py
import sqlite3

from config import DATABASE_PATH


def get_connection():
    """Establish a new SQLite connection with autocommit behavior.

    Returns:
        sqlite3.Connection: A database connection with autocommit enabled.
    """
    return sqlite3.connect(DATABASE_PATH, timeout=10, isolation_level=None)


def initialize_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS "tracked_users" (
            user_id_hash TEXT PRIMARY KEY,
            rank TEXT NOT NULL DEFAULT 'undefined'
        );
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS consent_log (
            id INTEGER PRIMARY KEY,
            user_id_enc TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY,
            user_id_hash TEXT NOT NULL,
            message_enc TEXT NOT NULL,
            row_hash TEXT NOT NULL UNIQUE
        );
        """
        )

        print("Database initialized (no-op if already exists).")
