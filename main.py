# main.py
"""
Discord bot for collecting and managing user consent.

- Registers and tracks consent using hashed/encrypted user IDs
- Offers interactive buttons to give or retract consent
- Writes logs and maintains registry via SQLite

Modules used:
- consent_registry.py: Handles storage of consent state and logs
- encryption.py: Provides AES encryption and SHA256 hashing for user IDs
"""


import logging
import os

import discord
from dotenv import load_dotenv

from consent_registry import consent_is_registered, register_consent, retract_consent
from encryption import encrypt, hash_user_id
from log_config import setup_logging

logger = logging.getLogger(__name__)
setup_logging()

# Load .env file and environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("SERVER_ID"))  # Must be int, not str

# Set up client and command tree
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    """Triggered when the bot is fully connected and ready."""
    # Register slash commands to a specific server (guild) for instant appearance
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("Slash commands synced to guild.")


class ConsentButton(discord.ui.View):
    """
    View presenting a consent button that registers the user's consent.
    """

    def __init__(self, *, timeout=180):
        """
        Initialize the consent button view.

        Args:
            timeout (int): Timeout in seconds before the view is disabled.
        """
        super().__init__(timeout=timeout)

    @discord.ui.button(label="I consent", style=discord.ButtonStyle.green)
    async def consent_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """
        Handle consent button press: encrypts and hashes user ID, registers consent.

        Args:
            interaction (discord.Interaction): The interaction context.
            button (discord.ui.Button): The button pressed.
        """
        user_id_hash = hash_user_id(str(interaction.user.id))
        enc_user_id = encrypt(str(interaction.user.id))
        register_consent(user_id_hash, enc_user_id)
        await interaction.response.edit_message(
            content="Your consent has been registered. Thanks!", view=None
        )


class RetractConsentButton(discord.ui.View):
    """
    View presenting a button to retract previously given consent.
    """

    def __init__(self, *, timeout=180):
        """
        Initialize the retraction button view.

        Args:
            timeout (int): Timeout in seconds before the view is disabled.
        """
        super().__init__(timeout=timeout)

    @discord.ui.button(label="I retract consent", style=discord.ButtonStyle.red)
    async def retract_consent_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """
        Handle retraction button press: encrypts and hashes user ID, removes consent.

        Args:
            interaction (discord.Interaction): The interaction context.
            button (discord.ui.Button): The button pressed.
        """
        try:
            user_id = str(interaction.user.id)
            user_id_hash = hash_user_id(user_id)
            enc_user_id = encrypt(user_id)
            retract_consent(user_id_hash, enc_user_id)
            await interaction.response.edit_message(
                content="Your consent has been retracted", view=None
            )
        except Exception as e:
            logger.critical(f"Consent retraction failed at UI level: {e}")
            await interaction.response.send_message(
                content="An error occurred while processing your retraction. Please try again later.",
                ephemeral=True,
            )


@tree.command(
    name="placeholder", description="placeholder", guild=discord.Object(id=GUILD_ID)
)
async def hello_command(interaction: discord.Interaction):
    """
    Slash command for showing consent status and the appropriate action button.

    Args:
        interaction (discord.Interaction): The interaction context.
    """
    user_id_hash = hash_user_id(str(interaction.user.id))
    if not consent_is_registered(user_id_hash):
        await interaction.response.send_message(
            "Your consent is not registered.", ephemeral=True, view=ConsentButton()
        )
    else:
        await interaction.response.send_message(
            "Your consent is registered.", ephemeral=True, view=RetractConsentButton()
        )


client.run(TOKEN)
