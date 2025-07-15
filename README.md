# Below Emerald Enthusiast

A privacy-focused Discord bot for opt-in message analysis, designed to collect anonymized questions and rank data from a single channel. Built for extracting coaching insights based on user rank and message topics, following GDPR principles.

---

## Features

- ✅ Slash command `/consent` for users to opt-in or retract consent.
- ✅ Collects highest self-assigned rank at time of consent.
- ✅ Encrypts message content (AES-256) and anonymizes users (SHA-256 hashing).
- ✅ Manual `/collect` command parses historical messages from a specific channel.
- ✅ Consent log and audit trail maintained.
- ✅ SQLite backend (PostgreSQL planned).
- ✅ Minimal required Discord permissions (bot + slash commands).
- ✅ Can be restricted to read a single channel via role permissions.

---

## Requirements

- Python 3.11+
- Discord bot token with `message_content` intent enabled.
- `.env` configuration file.
- Dependencies installed via:

```bash
pip install -r requirements.txt
```

---

## Setup Instructions

### 1. Clone Repo and Configure Environment

```bash
cp .env.example .env
```

Fill in:

- `DISCORD_TOKEN`
- `SERVER_ID`
- `CHANNEL_ID`
- `ENCRYPTION_KEY`
  *(Generate using: `python -c "import os; print(os.urandom(32).hex())"`)*
- Optional: adjust database or log paths.

---

### 2. Create Discord Bot Application

- Go to [Discord Developer Portal](https://discord.com/developers/applications).
- Create application and bot.
- go to Installation page
- Enable:
  - ✅ MESSAGE CONTENT INTENT,
  - ✅ SERVER MEMBERS INTENT
- in Guild Install, in scopes, add "bot"
- In installation contexts, make sure Guild Install is ticked.
- Install via "Install Link" -> Discord Provided Link.

---
### 3. Run the Bot

```bash
python main.py
```

---

## Usage

- `/consent` — Opens interactive UI to opt-in or withdraw.
- `/collect` — Parses message history from configured channel, but only for opted-in users.

---

## Database Schema Overview

### `tracked_users`
| Column        | Type   | Description                     |
|---------------|--------|---------------------------------|
| user_id_hash  | TEXT   | SHA-256 hash of user ID (PK)    |
| rank          | TEXT   | User’s highest self-assigned rank |

### `data`
| Column        | Type   | Description                         |
|---------------|--------|-------------------------------------|
| id            | INTEGER| Primary key                         |
| user_id_hash  | TEXT   | SHA-256 hashed user ID              |
| message_enc   | TEXT   | AES-256 encrypted message (Base64)  |
| row_hash      | TEXT   | Deduplication hash                  |

### `consent_log`
| Column        | Type   | Description                            |
|---------------|--------|----------------------------------------|
| id            | INTEGER| Primary key                            |
| user_id_enc   | TEXT   | AES-256 encrypted user ID              |
| action        | TEXT   | 'gave consent' or 'retracted consent'  |
| timestamp     | TEXT   | ISO-formatted timestamp                |

---

## Privacy & GDPR Compliance

- Messages are stored encrypted.
- Users remain anonymous (hashed IDs).
- Consent required before any data collection.
- Full deletion on consent withdrawal.
- No direct identifiers are stored.

---

## License

MIT License

---

## Author

Mads S. Balto  
[https://www.madsbalto.com](https://www.madsbalto.com)
