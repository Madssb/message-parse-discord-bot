# consent.py
import logging

import discord

from config import setup_logging
from consent_registry import consent_is_registered, register_consent, retract_consent
from encryption import encrypt, hash_user_id

logger = logging.getLogger(__name__)

setup_logging()

CONSENT_MESSAGE = (
    "**Why we're asking for consent**\n"
    "You're invited to contribute questions in #below-emerald to a fully anonymized study. The goal is to analyze trends by rank and champion for coaching insights.\n\n"
    "**We collect**\n"
    "- Message text\n"
    "- Champion and rank (if tagged)\n"
    "- Encrypted message and user IDs (so you can withdraw consent)\n\n"
    "Use the buttons below to opt in or out at any time."
)

ALREADY_CONSENTED_MESSAGE = (
    "✅ You're already on the consent list. You can retract your consent below."
)
NOT_CONSENTED_MESSAGE = (
    "ℹ️ You haven’t consented yet. Click below if you’d like to participate."
)

RETRACT_CONFIRMATION = (
    "🗑️ Your consent has been withdrawn and all related data has been deleted."
)
CONSENT_CONFIRMATION = "✅ Thanks! You've been added to the consent registry."


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

    @discord.ui.button(label="Give Consent", style=discord.ButtonStyle.green)
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
        await interaction.response.edit_message(content=CONSENT_CONFIRMATION, view=None)


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

    @discord.ui.button(label="Withdraw Consent", style=discord.ButtonStyle.red)
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
            user_id_hash = hash_user_id(str(interaction.user.id))
            enc_user_id = encrypt(str(interaction.user.id))
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


def setup_consent_commands(tree: discord.app_commands.CommandTree, guild_id: int):
    @tree.command(
        name="consent",
        description="Manage your consent for data collection in #below-emerald.",
        guild=discord.Object(id=guild_id),
    )
    async def consent_command(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_hash = hash_user_id(str(interaction.user.id))
        if not consent_is_registered(user_id_hash):
            await interaction.followup.send(
                NOT_CONSENTED_MESSAGE + "\n\n" + CONSENT_MESSAGE,
                ephemeral=True,
                view=ConsentButton(),
            )
        else:
            await interaction.followup.send(
                ALREADY_CONSENTED_MESSAGE,
                ephemeral=True,
                view=RetractConsentButton(),
            )
