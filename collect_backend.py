# collect_backend.py
import json
import logging
import sqlite3

import discord

from config import setup_logging
from consent_command import consent_is_registered
from encryption import compute_row_hash, encrypt, hash_user_id
from initialize_db import get_connection

logger = logging.getLogger(__name__)

setup_logging()


class MissingIntentsError(Exception):
    """Raised when message_content intent is not enabled."""

    pass


def js_r(filename: str):
    with open(filename) as f_in:
        return json.load(f_in)


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


def highest_rank_extractor(user_id_hash: str, guild: discord.Guild):
    """Returns highest rank for specified user id hash in specified guild.

    Args:
        user_id_hash (str): user id hash for who highest role in list is looked up
        guild (discord.Guild): Proper guild for getting role object

    Returns:
        str or None: The highest rank if exists and None if not."""
    ranks = [
        # "challenger",
        # "grandmaster",
        # "master",
        "Diamond",
        "Emerald",
        # "platinum",
        # "gold",
        # "silver",
        # "bronze",
        # "iron",
    ]
    role_ids = js_r("/home/madssb/mla-project/role_ids.json")
    for rank in ranks:
        role = guild.get_role(int(role_ids[rank]))
        if role:
            for member in role.members:
                if user_id_hash == hash_user_id(str(member.id)):
                    return rank
    return None


def insert_rank(user_id_hash: str, guild: discord.Guild):
    """Update a user's rank in tracked_users based on Discord guild data."""
    try:
        rank = highest_rank_extractor(user_id_hash, guild)
        with get_connection() as con:
            cur = con.cursor()
            cur.execute(
                "UPDATE tracked_users SET rank = ? WHERE user_id_hash = ?",
                (rank, user_id_hash),
            )
        logger.debug(f"Updated rank to '{rank}' for user hash {user_id_hash[:6]}...")
    except Exception as e:
        logger.error(f"Failed to update rank for user hash {user_id_hash[:6]}: {e}")


def get_all_user_hashes() -> list[str]:
    """Fetch all user_id_hash entries from tracked_users."""
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("SELECT user_id_hash FROM tracked_users")
        rows = cur.fetchall()
        return [row[0] for row in rows]


async def batch_update_ranks(guild: discord.Guild):
    """Batch update all users' ranks in a single transaction."""
    try:
        user_id_hashes = get_all_user_hashes()
        ranks = [
            highest_rank_extractor(user_id_hash, guild)
            for user_id_hash in user_id_hashes
        ]
        ranks_to_update = [
            (rank, user_id_hash) for rank, user_id_hash in zip(ranks, user_id_hashes)
        ]
        with get_connection() as con:
            cur = con.cursor()
            cur.executemany(
                "UPDATE tracked_users SET rank = ? WHERE user_id_hash = ?",
                ranks_to_update,
            )
            logger.debug(f"Batch updated ranks for {len(ranks_to_update)} users.")
    except Exception as e:
        logger.critical(f"Failed batch rank update: {e}")
        raise


async def message_parser(channel: discord.TextChannel):
    """Parse and store messages from a Discord channel if user consent exists.

    Args:
        channel (discord.TextChannel): The channel to scrape messages from.
        guild: (discord.Guild): Guild whos user roles in consented message collection is parsed for highest rank.

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
