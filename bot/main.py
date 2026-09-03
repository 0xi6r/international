import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import BOT_TOKEN
from .callbacks import button
from .handlers import (
    admin,
    broadcast_message,
    error_handler,
    handle_message,
    help_command,
    recent_errors,
    start,
    stats,
)

############################################################
# Logging
############################################################

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

############################################################
# Build Application
############################################################

def build_application():
    """Build a short-lived application for one webhook invocation."""
    app = ApplicationBuilder().token(BOT_TOKEN).updater(None).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("msg", broadcast_message))
    app.add_handler(CommandHandler("errors", recent_errors))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    return app

############################################################
# Startup
############################################################

def main():

    logger.info(
        "Starting Article Reader Bot..."
    )

    build_application().run_polling(
        allowed_updates=None,
    )


if __name__ == "__main__":
    main()
