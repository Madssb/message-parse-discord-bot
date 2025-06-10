# Discord Consent Bot

This bot collects anonymized consent and message data from a designated channel for analysis purposes (e.g., coaching insights). It follows GDPR principles and provides opt-in/opt-out via Discord slash commands and UI buttons.

## Features

- ✅ Slash command `/consent` for users to give or withdraw consent.
- ✅ Consent logs and encrypted user IDs stored in `project_data.db`.
- ✅ Slash command `/collect` for parsing historical messages from a specific channel.
- ✅ Fully anonymized: only hashed IDs and AES-encrypted content are stored.
- ✅ SQLite backend; no external services required.
- ✅ Minimal required Discord permissions (Scope: bot).
- ✅ Bot access can be fully restricted to a single channel via role permissions:
  - Create a custom role with no permissions.
  - Assign it to the bot.
  - Grant that role read access only in the desired channel.

---

## Requirements

- Python 3.10+
- Discord bot token
- `message_content` intent **enabled** in the [Discord Developer Portal](https://discord.com/developers/applications)
- The following Python dependencies (install with pip):

```bash
pip install -r requirements.txt
```

---

## Setup

### 1. Create `.env` from Template

```bash
cp .env.example .env
```

Fill in the following variables:

- `DISCORD_TOKEN=<your bot token>`
- `SERVER_ID=<your server (guild) ID>`
- `CHANNEL_ID=<channel ID for parsing>`
- `ENCRYPTION_KEY=<32-byte AES key in hex>`

To generate a valid encryption key:

```bash
python -c "import os; print(os.urandom(32).hex())"
```

---

### 2. Create Bot Application

1. Visit [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application
3. Under **Bot → Privileged Gateway Intents**, enable:
   - ✅ Message Content Intent

4. Under **OAuth2 → URL Generator**:
   - Scopes: `bot`

Use the generated URL to invite the bot to your server.

---

### 3. Initialize the Database

Before running the bot, create required tables:

```bash
python initialize_db.py
```

This creates:

- `consent_registry`
- `consent_log`
- `data` (for collected message records)

---

## Usage

Start the bot with:

```bash
python main.py
```

### Slash Commands

- `/consent` — Opens a consent interface with buttons to opt-in or out.
- `/collect` — Triggers message parsing in the configured channel. Only collects from users who have consented.

---

## Notes

- Only one channel is read (as configured in `.env`).
- Data is stored in `project_data.db`, which should **not** be committed. It’s gitignored.
- This bot does not request Administrator or excessive permissions.
- All logic is local and transparent. Tokens and keys are stored only in your local environment.
- To restrict the bot’s access to a single channel:
  - Create a role with no base permissions.
  - Assign this role to the bot.
  - In the target channel’s settings, allow this role to “Read Messages”.
  - Ensure no other roles or permissions grant the bot access elsewhere.

---

## License

MIT
