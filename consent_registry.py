# consent_registry.py
"""Consent registration and logging system for Discord users.

This module manages a consent registry and a corresponding consent log,
both backed by an SQLite database. It ensures:
- User IDs are hashed for lookup (privacy-preserving),
- Encrypted user IDs are stored in the log for auditability,
- Logging is controlled via Python's logging module.

Encryption and hashing are handled externally via `encryption.py`.

Tables:
- consent_registry(user_id_hash TEXT PRIMARY KEY)
- consent_log(id INTEGER, user_id_enc TEXT, action TEXT, timestamp TEXT)
"""
import logging
import sqlite3
from datetime import datetime
from typing import Literal

from log_config import setup_logging

logger = logging.getLogger(__name__)
setup_logging()


con = sqlite3.connect("project_data.db")
cur = con.cursor()


# instantiate consent_registry
def assert_table_exists(table_name: str):
    res = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    if res.fetchone() is None:
        raise RuntimeError(f"Required table '{table_name}' is missing in the database.")


assert_table_exists("consent_registry")
assert_table_exists("consent_log")


def log_consent(
    user_id_hash: str,
    enc_user_id: str,
    action: Literal["gave consent", "retracted consent"],
) -> None:
    """Log a consent action to the consent_log table.

    Args:
        user_id_hash (str): Hashed user ID, used only for logging/debugging context.
        enc_user_id (str): Encrypted user ID for audit trail.
        action (Literal): Action performed — "gave consent" or "retracted consent".

    Raises:
        ValueError: If the action is not a valid consent operation.
    """
    if action not in {"gave consent", "retracted consent"}:
        logger.critical(
            f"Invalid action. Expected 'gave consent' or 'retracted consent', got: {action}."
        )
    try:
        timestamp = datetime.now().isoformat()
        cur.execute(
            "INSERT INTO consent_log (user_id_enc, action, timestamp) VALUES (?, ?, ?)",
            (enc_user_id, action, timestamp),
        )
        con.commit()
        logger.debug(
            f"Added consent_registry entry for user hash {user_id_hash[:6]}..."
        )
    except Exception as e:
        logger.critical(
            f"Failed to add consent_registry entry for user hash {user_id_hash[:6]}...: {e}"
        )
        raise e


def register_consent(user_id_hash: str, enc_user_id: str) -> None:
    """Register a user's consent by inserting their hash into the registry.

    Also logs the action to the consent log.

    Args:
        user_id_hash (str): Hashed user ID for privacy-safe lookup.
        enc_user_id (str): Encrypted user ID for logging.
    """
    try:
        cur.execute(
            "INSERT INTO consent_registry(user_id_hash) VALUES (?)", (user_id_hash,)
        )
        con.commit()
        logger.debug(
            f"Added consent_registry entry for user hash {user_id_hash[:6]}..."
        )
        log_consent(user_id_hash, enc_user_id, "gave consent")
    except Exception as e:
        logger.error(
            f"Failed to add consent_registry entry for user hash {user_id_hash[:6]}...: {e}"
        )


def retract_consent(user_id_hash: str, enc_user_id: str) -> None:
    """Remove a user's consent and associated data from the registry and logs."""
    try:
        # Delete from consent_registry
        cur.execute(
            "DELETE FROM consent_registry WHERE user_id_hash = ?", (user_id_hash,)
        )
        # Delete associated message records
        cur.execute("DELETE FROM data WHERE user_id_hash = ?", (user_id_hash,))

        con.commit()

        logger.debug(
            f"Deleted consent_registry and data entries for hash {user_id_hash[:6]}..."
        )
        log_consent(user_id_hash, enc_user_id, "retracted consent")
    except Exception as e:
        logger.critical(
            f"Consent retraction failed for hash {user_id_hash[:6]}...: {e}"
        )
        raise e


def consent_is_registered(user_id_hash: str) -> bool:
    """Check whether a user has a consent record in the registry.

    Args:
        user_id_hash (str): Hashed user ID to look up.

    Returns:
        bool: True if the user has given consent, False otherwise.
    """
    try:
        res = cur.execute(
            "SELECT 1 FROM consent_registry WHERE user_id_hash = ?", (user_id_hash,)
        )
        found = res.fetchone() is not None
        logger.debug(
            f"Checked consent for hash {user_id_hash[:6]}...: {'found' if found else 'not found'}"
        )
        return found
    except Exception as e:
        logger.critical(f"Failed to check consent for hash {user_id_hash[:6]}...: {e}")
        raise e
