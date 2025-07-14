# config.py
"""Handle environment variables in a way that avoids circular imports, and define logging behavior"""
import logging
import os

from dotenv import load_dotenv

if os.getenv("ENVIRONMENT") != "railway":
    load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("SERVER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH")


LOGFILE_PATH = os.getenv("LOGFILE_PATH")


def setup_logging(level: int = logging.DEBUG):

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOGFILE_PATH, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
