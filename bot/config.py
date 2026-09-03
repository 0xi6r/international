import os
import re

from dotenv import load_dotenv

############################################################
# Load Environment
############################################################

load_dotenv()

############################################################
# Telegram
############################################################

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN not found in .env"
    )

############################################################
# Admin
############################################################

ADMIN_ID = int(
    os.getenv("ADMIN_ID", "0")
)

############################################################
# Article Endpoint
############################################################

ARTICLE_ENDPOINT = os.getenv("ARTICLE_ENDPOINT")

if not ARTICLE_ENDPOINT:
    raise RuntimeError(
        "ARTICLE_ENDPOINT not found in .env"
    )

############################################################
# Bot Settings
############################################################

MAX_MESSAGE_LENGTH = 3800

URL_REGEX = re.compile(
    r"https?://\S+"
)

############################################################
# Logging
############################################################

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
).upper()
