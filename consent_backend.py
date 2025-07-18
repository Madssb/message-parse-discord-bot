# consent_backend.py
import logging
import sqlite3
from datetime import datetime
from typing import Literal

from config import setup_logging
from initialize_db import get_connection

logger = logging.getLogger(__name__)

setup_logging()


def log_consent(
    user_id_hash: str,
    enc_user_id: str,
    action: Literal["gave consent", "retracted consent"],
) -> None:
    """Write a consent-related action to the audit log table.

    Args:
        user_id_hash (str): Hashed user ID for logging context.
        enc_user_id (str): Encrypted user ID for audit trail.
        action (Literal): Either 'gave consent' or 'retracted consent'.

    Raises:
        Exception: On database insertion failure.
    """
    if action not in {"gave consent", "retracted consent"}:
        logger.critical(
            f"Invalid action. Expected 'gave consent' or 'retracted consent', got: {action}."
        )
        return

    try:
        timestamp = datetime.now().isoformat()
        with get_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO consent_log (user_id_enc, action, timestamp) VALUES (?, ?, ?)",
                (enc_user_id, action, timestamp),
            )
        logger.debug(f"Logged action '{action}' for hash {user_id_hash[:6]}...")
    except Exception as e:
        logger.critical(f"Failed to log consent action for {user_id_hash[:6]}: {e}")
        raise


def register_consent(user_id_hash: str, enc_user_id: str) -> None:
    """Add a user to the consent registry if not already present.

    Also logs the action to the consent_log.

    Args:
        user_id_hash (str): Hashed user ID for privacy-preserving storage.
        enc_user_id (str): Encrypted user ID for auditability.

    Raises:
        Exception: On unexpected database failure.
    """
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO tracked_users(user_id_hash) VALUES (?)",
                (user_id_hash,),
            )
        logger.debug(f"Registered consent for hash {user_id_hash[:6]}...")
        log_consent(user_id_hash, enc_user_id, "gave consent")
    except sqlite3.IntegrityError:
        logger.debug(
            f"Consent already exists for hash {user_id_hash[:6]} — skipping insert."
        )
    except Exception as e:
        logger.error(f"Consent registration failed for hash {user_id_hash[:6]}: {e}")
        raise


def retract_consent(user_id_hash: str, enc_user_id: str) -> None:
    """Remove a use's consent and associated data records.

    This deletes entries from both the `tracked_users` and `data` tables.
    Also logs the action to the audit log.

    Args:
        user_id_hash (str): Hashed user ID to delete.
        enc_user_id (str): Encrypted ID for logging.

    Raises:
        Exception: If any deletion or logging operation fails.
    """
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute(
                "DELETE FROM tracked_users WHERE user_id_hash = ?", (user_id_hash,)
            )
            cur.execute("DELETE FROM data WHERE user_id_hash = ?", (user_id_hash,))
        logger.debug(
            f"Retracted consent and deleted data for hash {user_id_hash[:6]}..."
        )
        log_consent(user_id_hash, enc_user_id, "retracted consent")
    except Exception as e:
        logger.critical(f"Consent retraction failed for hash {user_id_hash[:6]}: {e}")
        raise


def consent_is_registered(user_id_hash: str) -> bool:
    """Check if a user has an active consent entry.

    Args:
        user_id_hash (str): Hashed user ID to query.

    Returns:
        bool: True if consent exists, False otherwise.

    Raises:
        Exception: On database query failure.
    """
    try:
        with get_connection() as con:
            cur = con.cursor()
            res = cur.execute(
                "SELECT 1 FROM tracked_users WHERE user_id_hash = ?",
                (user_id_hash,),
            )
            found = res.fetchone() is not None
        logger.debug(
            f"Checked consent for hash {user_id_hash[:6]}: {'found' if found else 'not found'}"
        )
        return found
    except Exception as e:
        logger.critical(f"Failed to check consent for hash {user_id_hash[:6]}: {e}")
        raise
