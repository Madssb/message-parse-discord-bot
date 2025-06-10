# consent.py
import hashlib
import logging
import sqlite3

import discord

from consent_registry import consent_is_registered
from encryption import encrypt, hash_user_id
from log_config import setup_logging

logger = logging.getLogger(__name__)
setup_logging()


def get_connection():
    """Establish a new SQLite connection with autocommit behavior.

    Returns:
        sqlite3.Connection: A database connection with autocommit enabled.
    """
    return sqlite3.connect("project_data.db", timeout=10, isolation_level=None)


class MissingIntentsError(Exception):
    """Raised when message_content intent is not enabled."""

    pass


def assert_table_exists(table_name: str):
    """Ensure the specified table exists in the database.

    Args:
        table_name (str): The name of the table to check.

    Raises:
        RuntimeError: If the table is missing.
    """
    with get_connection() as con:
        cur = con.cursor()
        res = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if res.fetchone() is None:
            raise RuntimeError(
                f"Required table '{table_name}' is missing in the database."
            )


assert_table_exists("data")


def compute_row_hash(user_id_hash: str, message_enc: str) -> str:
    """Create a SHA-256 hash from a user hash and encrypted message.

    Args:
        user_id_hash (str): Hashed user ID.
        message_enc (str): Encrypted message content.

    Returns:
        str: A SHA-256 hex digest representing the row hash.
    """
    combined = user_id_hash + message_enc
    return hashlib.sha256(combined.encode()).hexdigest()


def insert_message(user_id_hash: str, message_enc: str, row_hash: str):
    """Insert a message record into the data table.

    Args:
        user_id_hash (str): Hashed user ID.
        message_enc (str): Encrypted message content.
        row_hash (str): Unique hash of the record.
    """
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO data (user_id_hash, message_enc, row_hash) VALUES (?, ?, ?)",
                (user_id_hash, message_enc, row_hash),
            )
        logger.debug(f"Added data entry for user hash {user_id_hash[:6]}...")
    except sqlite3.IntegrityError:
        logger.debug(
            f"Duplicate data entry detected for hash {user_id_hash[:6]} — skipping insert."
        )
    except Exception as e:
        logger.error(f"Failed to add data entry for user hash {user_id_hash[:6]}: {e}")


async def message_parser(channel: discord.TextChannel):
    """Parse and store messages from a Discord channel if user consent exists.

    Args:
        channel (discord.TextChannel): The channel to scrape messages from.

    Raises:
        MissingIntentsError: If message content is inaccessible due to missing intent.
    """
    async for message in channel.history(limit=None):
        if not message.content:
            logger.critical(
                "message.content is empty — did you enable the Message Content Intent?"
            )
            raise MissingIntentsError(
                "message.content is empty. You likely forgot to enable the Message Content Intent "
                "in the Discord Developer Portal (Bot → Privileged Gateway Intents)."
            )
        user_id_hash = hash_user_id(str(message.author.id))
        if consent_is_registered(user_id_hash):
            message_enc = encrypt(message.content)
            row_hash = compute_row_hash(user_id_hash, message.content)
            insert_message(user_id_hash, message_enc, row_hash)


def setup_message_parse_command(
    tree: discord.app_commands.CommandTree, channel: discord.TextChannel, guild_id: int
):
    """Register the /collect command to parse messages from a specific channel.

    Args:
        tree (discord.app_commands.CommandTree): The app command tree to register to.
        channel (discord.TextChannel): The channel whose messages will be collected.
        guild_id (int): Guild ID for command scoping.
    """

    @tree.command(
        name="collect",
        description="Collects messages from channel",
        guild=discord.Object(id=guild_id),
    )
    async def collect_command(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Collecting messages...", ephemeral=True)
        await message_parser(channel)
        await interaction.followup.send("Message collection complete.", ephemeral=True)
