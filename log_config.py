# log_config.py
import logging
import os

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
