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
con = sqlite3.connect("project_data.db")
cur = con.cursor()


class MissingIntentsError(Exception):
    """Raised when message_content intent is not enabled."""

    pass


# instantiate consent_registry
def assert_table_exists(table_name: str):
    res = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    if res.fetchone() is None:
        raise RuntimeError(f"Required table '{table_name}' is missing in the database.")


assert_table_exists("data")


def compute_row_hash(user_id_hash: str, message_enc: str) -> str:
    combined = user_id_hash + message_enc
    return hashlib.sha256(combined.encode()).hexdigest()


def insert_message(user_id_hash: str, message_enc: str, row_hash: str):
    try:

        cur.execute(
            "INSERT INTO data (user_id_hash, message_enc, row_hash) VALUES (?, ?, ?)",
            (user_id_hash, message_enc, row_hash),
        )
        con.commit()
        logger.debug(f"Added data entry for user hash {user_id_hash[:6]}...")
    except Exception as e:
        logger.error(
            f"Failed to add data entry for user hash {user_id_hash[:6]}...: {e}"
        )


async def message_parser(channel: discord.TextChannel):
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
            row_hash = compute_row_hash(user_id_hash, message_enc)
            insert_message(user_id_hash, message_enc, row_hash)


def setup_message_parse_command(
    tree: discord.app_commands.CommandTree, channel: discord.TextChannel, guild_id: int
):
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
