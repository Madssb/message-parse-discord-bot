# collect_command.py
import json
import logging
import sqlite3

import discord
from discord import app_commands

from collect_backend import batch_update_ranks, message_parser
from config import COLLECT_PASSWORD, GUILD_ID, setup_logging

logger = logging.getLogger(__name__)
setup_logging()


def setup_collect_command(
    tree: discord.app_commands.CommandTree,
    channel: discord.TextChannel,
    guild: discord.Guild,
):
    """Register the /collect command to parse messages from a specific channel.

    Args:
        tree (discord.app_commands.CommandTree): The app command tree to register to.
        channel (discord.TextChannel): The channel whose messages will be collected.
        guild: (discord.Guild): Guild whos user roles in consented message collection is parsed for highest rank.
    """

    @tree.command(
        name="collect",
        description="Collects messages from channel",
        guild=discord.Object(id=GUILD_ID),
    )
    @app_commands.describe(password="Password required to execute command.")
    async def collect_command(interaction: discord.Interaction, password: str):
        if password != COLLECT_PASSWORD:
            await interaction.response.send_message(
                "❌ Incorrect password. Access denied.", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Collecting messages...", ephemeral=True)
        await message_parser(channel)
        await batch_update_ranks(guild)
        await interaction.followup.send("Message collection complete.", ephemeral=True)
