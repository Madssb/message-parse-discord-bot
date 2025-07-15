# main.py
import logging

import discord

from collect_command import setup_collect_command
from config import CHANNEL_ID, GUILD_ID, TOKEN, setup_logging
from consent_command import setup_consent_commands
from initialize_db import initialize_db

logger = logging.getLogger(__name__)

setup_logging()
initialize_db()


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    tree.clear_commands(guild=discord.Object(id=GUILD_ID))
    channel = client.get_channel(CHANNEL_ID)
    guild = client.get_guild(GUILD_ID)
    setup_consent_commands(tree)
    setup_collect_command(tree, channel, guild)
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    logger.info(f"Logged in as {client.user} (ID: {client.user.id})")
    logger.info("Slash commands synced.")


if __name__ == "__main__":
    client.run(TOKEN)
