import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from article import fetch_article
from storage import db

from .config import (
    ADMIN_ID,
    MAX_MESSAGE_LENGTH,
    URL_REGEX,
)

from .supported import (
    SUPPORTED_PUBLISHERS,
    get_publisher,
)

from .ui import (
    build_header,
    help_text,
    main_menu,
    send_html,
    update_status,
    welcome_text,
)

logger = logging.getLogger(__name__)

REPORT_URL = "https://t.me/articlereaderbotinfo?direct"
BROADCAST_PREFIX = "📢 Bot Update\n\n"
BROADCAST_LIMIT = 4096 - len(BROADCAST_PREFIX)


def command_payload(text: str) -> str:

    parts = text.split(
        maxsplit=1,
    )

    if len(parts) < 2:
        return ""

    payload = parts[1].strip()

    if (
        len(payload) >= 2
        and payload[0] == payload[-1]
        and payload[0] in ("'", '"')
    ):

        payload = payload[1:-1].strip()

    return payload


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    db.register_user(update.effective_user)

    logger.info(
        "User %s started the bot",
        update.effective_user.id,
    )

    await update.message.reply_text(
        welcome_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu(),
        disable_web_page_preview=True,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    db.register_user(update.effective_user)

    await update.message.reply_text(
        help_text(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    db.register_user(update.effective_user)

    user = db.user_stats(
        update.effective_user.id
    )

    if user is None:

        await update.message.reply_text(
            "📊 <b>Your Usage</b>\n\n"
            "No usage data is available yet.",
            parse_mode=ParseMode.HTML,
        )

        return

    text = (
        "📊 <b>Your Usage</b>\n\n"
        f"📖 Articles Read: <b>{user['articles_read']}</b>\n"
        f"📨 Requests: <b>{db.user_requests(update.effective_user.id)}</b>\n"
        f"✅ Successful: <b>{db.user_successful_requests(update.effective_user.id)}</b>\n"
        f"❌ Failed: <b>{db.user_failed_requests(update.effective_user.id)}</b>\n\n"
        f"🗓 Joined: <code>{user['joined_at']}</code>\n"
        f"Last Seen: <code>{user['last_seen']}</code>"
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ NOT FOUND."
        )

        return

    publishers = db.top_publishers()

    if publishers:

        publisher_text = "\n".join(
            f"• {row['domain']} ({row['total']})"
            for row in publishers
        )

    else:

        publisher_text = "No data available."

    text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 Users: <b>{db.total_users()}</b>\n"
        f"📖 Articles Read: <b>{db.total_articles()}</b>\n"
        f"📨 Requests: <b>{db.total_requests()}</b>\n"
        f"🔥 Today: <b>{db.today_requests()}</b>\n"
        f"✅ Successful: <b>{db.successful_requests()}</b>\n"
        f"❌ Failed: <b>{db.failed_requests()}</b>\n\n"
        '<b>Broadcast</b>\n'
        '<code>/msg "message here"</code>\n\n'
        "<b>Top Publishers</b>\n"
        f"{publisher_text}"
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ NOT FOUND."
        )

        return

    payload = command_payload(
        update.message.text or ""
    )

    if not payload:

        await update.message.reply_text(
            'Usage: /msg "message here"'
        )

        return

    if len(payload) > BROADCAST_LIMIT:

        await update.message.reply_text(
            f"❌ Message is too long. Limit: {BROADCAST_LIMIT} characters."
        )

        return

    user_ids = db.all_user_ids()

    if not user_ids:

        await update.message.reply_text(
            "No registered users found."
        )

        return

    sent = 0
    failed = 0
    text = BROADCAST_PREFIX + payload

    for telegram_id in user_ids:

        try:

            await context.bot.send_message(
                chat_id=telegram_id,
                text=text,
                disable_web_page_preview=True,
            )

            sent += 1

        except Exception as e:

            failed += 1

            logger.warning(
                "Failed broadcasting to %s: %s",
                telegram_id,
                e,
            )

    await update.message.reply_text(
        "Broadcast complete.\n\n"
        f"Sent: {sent}\n"
        f"Failed: {failed}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if not message:
        return

    db.register_user(update.effective_user)

    if not message.text:

        await message.reply_text(
            "❌ Please send an article URL."
        )

        return

    match = URL_REGEX.search(message.text)

    if not match:

        await message.reply_text(
            "❌ Please send a valid article URL."
        )

        return

    url = match.group()

    publisher = get_publisher(url)

    if publisher is None:

        supported = [
            f'• <a href="{item["website"]}">{item["name"]}</a>'
            for item in SUPPORTED_PUBLISHERS.values()
        ]

        await message.reply_text(
            "❌ <b>Unsupported Publisher</b>\n\n"
            "This publisher isn't supported yet.\n\n"
            "<b>Supported publishers</b>\n\n"
            + "\n".join(supported)
            + "\n\nMore publishers will be added over time.",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        return

    logger.info(
        "User %s requested %s",
        update.effective_user.id,
        url,
    )

    status = await message.reply_text(
        "📡 Contacting server..."
    )

    try:

        await update_status(
            status,
            "⬇️ Downloading article..."
        )

        article = await fetch_article(url)

        db.increment_articles(
            update.effective_user.id
        )

        db.log_request(
            telegram_id=update.effective_user.id,
            url=url,
            title=article["title"],
            success=True,
        )

        logger.info(
            "Successfully fetched '%s'",
            article["title"],
        )

        header = build_header(article)

        await update_status(
            status,
            "🧹 Cleaning article..."
        )

        image_count = sum(
            1
            for block in article["blocks"]
            if (
                block["type"] == "image"
                and not block.get("is_hero")
            )
        )

        if article.get("hero_image"):
            image_count += 1

        await update_status(
            status,
            f"🖼 Processing {image_count} image(s)..."
        )

        await update_status(
            status,
            "📤 Sending article..."
        )

        await send_html(
            message,
            header,
        )

        if article.get("hero_image"):

            try:

                await message.reply_photo(
                    photo=article["hero_image"],
                )

            except Exception as e:

                logger.warning(
                    "Failed sending hero image: %s",
                    e,
                )

        buffer = ""

        for block in article["blocks"]:

            if block["type"] == "heading":

                if buffer:

                    await send_html(
                        message,
                        buffer,
                    )

                    buffer = ""

                await send_html(
                    message,
                    f"<b>{block['html']}</b>",
                )

            elif block["type"] == "quote":

                if buffer:

                    await send_html(
                        message,
                        buffer,
                    )

                    buffer = ""

                await send_html(
                    message,
                    f"<blockquote>{block['html']}</blockquote>",
                )

            elif block["type"] == "paragraph":

                text = block["html"] + "\n\n"

                if (
                    len(buffer) + len(text)
                    > MAX_MESSAGE_LENGTH
                ):

                    await send_html(
                        message,
                        buffer,
                    )

                    buffer = text

                else:

                    buffer += text

            elif block["type"] == "list":

                text = "\n".join(
                    block["items"]
                ) + "\n\n"

                if (
                    len(buffer) + len(text)
                    > MAX_MESSAGE_LENGTH
                ):

                    await send_html(
                        message,
                        buffer,
                    )

                    buffer = text

                else:

                    buffer += text

            elif block["type"] == "image":

                if block.get("is_hero"):
                    continue

                if buffer:

                    await send_html(
                        message,
                        buffer,
                    )

                    buffer = ""

                try:

                    caption = block.get(
                        "caption",
                        "",
                    )

                    if len(caption) > 1024:

                        caption = (
                            caption[:1020]
                            + "..."
                        )

                    await message.reply_photo(
                        photo=block["url"],
                        caption=caption or None,
                    )

                except Exception as e:

                    logger.warning(
                        "Failed sending image: %s",
                        e,
                    )

        if buffer:

            await send_html(
                message,
                buffer,
            )

        await status.delete()

    except Exception as e:

        logger.exception(
            "Failed fetching article."
        )

        db.log_request(
            telegram_id=update.effective_user.id,
            url=url,
            title="",
            success=False,
        )

        try:

            await status.edit_text(
                "❌ <b>Unable to get the article, TRY AGAIN.</b>\n\n"
                "Issue might be the upstream source or our backend  "
                "If this persists after trying again.\n\n"
                "Please report this article so it can be made available.\n\n"
                f"👉 {REPORT_URL}",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )

        except Exception:

            await message.reply_text(
                "❌ <b>Unable to retrieve the article.</b>\n\n"
                "The article was automatically retried 3 times but "
                "could not be processed.\n\n"
                "Please report this article so it can be investigated and made available.\n\n"
                f"👉 {REPORT_URL}",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
