from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode

############################################################
# Keyboards
############################################################

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "📖 How to Use",
                callback_data="help",
            )
        ],

        [
            InlineKeyboardButton(
                "🌍 Supported Sources",
                callback_data="publishers",
            )
        ],

        [
            InlineKeyboardButton(
                "❤️ Sponsor",
                callback_data="sponsor",
            )
        ],

        [
            InlineKeyboardButton(
                "ℹ️ About",
                callback_data="about",
            )
        ],

    ]

    return InlineKeyboardMarkup(keyboard)


def back_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="home",
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


############################################################
# Telegram Helpers
############################################################

async def send_html(message, text: str):

    """
    Sends HTML safely.
    """

    if not text.strip():
        return

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def update_status(status_message, text):

    """
    Safely edits the progress message.
    """

    try:

        await status_message.edit_text(text)

    except Exception:

        pass


############################################################
# Article Formatting
############################################################

def build_header(article):

    """
    Builds the article header shown before
    the article body.
    """

    header = ""

    if article.get("title"):

        header += (
            f"<b>{article['title']}</b>\n"
        )

    if article.get("subtitle"):

        header += (
            f"<i>{article['subtitle']}</i>\n\n"
        )

    if article.get("author"):

        header += (
            f"👤 {article['author']}\n"
        )

    if article.get("date"):

        header += (
            f"📅 {article['date']}"
        )

    return header.strip()


############################################################
# Menus
############################################################

def welcome_text():

    return (
        "📰 <b>Welcome to Article Reader Bot</b>\n\n"

        "Read <b>PAYWALLED</b> articles from supported sources <b>ONLY</b>.\n\n"

        "Simply send an article URL and the bot will:\n\n"

        "• Retrieve the article\n"
        "• Remove unnecessary clutter\n"
        "• Preserve formatting\n"
        "• Keep embedded images\n"
        "• Preserve hyperlinks\n\n"

        "Choose an option below to learn more."
    )


def help_text():

    return (
        "<b>📖 How to Use</b>\n\n"

        "1. Copy an article URL.\n"

        "2. Paste it into this chat.\n\n"

        "3. Wait a few seconds while the article is processed.\n\n"

        "4. Enjoy a clean reading experience.\n\n"

        "Use /stats to view your usage.\n\n"

        "<b>Supported Content</b>\n"

        "• Images\n"
        "• Hyperlinks\n"
        "• Headings\n"
        "• Quotes\n"
        "• Lists\n"
        "• Rich formatting"
    )


def about_text():

    return (
        "<b>ℹ️ About</b>\n\n"

        "Article Reader Bot makes reading online articles inside Telegram simple and distraction-free.\n\n"
        "Join our channel to get updates on new sources and features: https://t.me/articlereaderbotinfo\n\n"
        "Features include:\n\n"

        "• Clean article formatting\n"
        "• Embedded images\n"
        "• Hyperlinks\n"
        "• Fast article retrieval\n"
        "• Automatic cleanup\n\n"

        "Made with ❤️ for readers."
    )


def publishers_text():

    return (
        "<b>🌍 Supported Sources</b>\n\n"

        "The bot ONLY works with these publishers:\n\n"

        "• Financial Times\n"
        "• Bloomberg\n"
        "• Medium\n"
        "• New York Times\n"
        "• The Economist\n"
        "• Washington Post\n"
        "• Reuters\n\n"

        "Support for additional publishers continues to improve over time."
    )


def sponsor_text():

    return (
        "<b>❤️ Support the Project</b>\n\n"

        "If this bot has been useful and you'd like to support its continued development, donations are greatly appreciated.\n\n"

        "<b>GRAM</b>\n"
        "<code>UQATkjn7oWrl7nh7HgTiIw2uOwxzx96oUzoBGFDmuw0a5ap2</code>\n\n"

        "<b>Bitcoin (BTC)</b>\n"
        "<code>bc1qw8nfxmzesh84ve9sv7khlvqv767newpw2gu6ca</code>\n\n"

        "<b>Ethereum (ETH)</b>\n"
        "<code>0x2772aE66934c0d0151d5878003Ea732B7a228815</code>\n\n"

        "<b>SOLANA (SOL)</b>\n"
        "<code>8DqxGeScUDEqeuHPprmU8md2z2ZkDfwqePnrhiVAJyzx</code>\n\n"

        "Every contribution helps adds more paywalled sources.\n\n"

        "Thank you ❤️"
    )
