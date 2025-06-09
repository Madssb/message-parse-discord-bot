# main.py
import os

import discord
from dotenv import load_dotenv

from consent import setup_consent_commands
from log_config import setup_logging

setup_logging()
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("SERVER_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

setup_consent_commands(tree, GUILD_ID)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("Slash commands synced.")


client.run(TOKEN)
