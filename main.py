# main.py
import logging
import os

import discord
from dotenv import load_dotenv

from consent import setup_consent_commands
from initialize_db import initialize_db
from log_config import setup_logging
from message_parser import setup_message_parse_command

logger = logging.getLogger(__name__)
setup_logging()
initialize_db()
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("SERVER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    tree.clear_commands(guild=discord.Object(id=GUILD_ID))
    channel = client.get_channel(CHANNEL_ID)
    setup_consent_commands(tree, GUILD_ID)
    setup_message_parse_command(tree, channel, GUILD_ID)
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    logger.info(f"Logged in as {client.user} (ID: {client.user.id})")
    logger.info("Slash commands synced.")


if __name__ == "__main__":
    client.run(TOKEN)
