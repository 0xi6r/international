import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from storage import db

from .broadcast import send_broadcast
from .config import ADMIN_ID
from .ui import (
    about_text,
    back_menu,
    help_text,
    main_menu,
    publishers_text,
    sponsor_text,
    welcome_text,
)

logger = logging.getLogger(__name__)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    ###########################################################
    # BROADCAST
    ###########################################################

    if query.data.startswith("broadcast:"):

        if query.from_user.id != ADMIN_ID:

            await query.message.reply_text(
                "❌ NOT FOUND."
            )

            return

        parts = query.data.split(":")

        if len(parts) != 3:

            await query.edit_message_text(
                "Invalid broadcast action."
            )

            return

        action = parts[1]
        try:

            broadcast_id = int(parts[2])

        except ValueError:

            await query.edit_message_text(
                "Invalid broadcast action."
            )

            return

        if action == "cancel":

            if db.cancel_broadcast(broadcast_id):

                await query.edit_message_text(
                    "Broadcast cancelled."
                )

            else:

                await query.edit_message_text(
                    "Broadcast is no longer pending."
                )

            return

        if action == "send":

            broadcast = db.claim_broadcast(broadcast_id)

            if broadcast is None:

                await query.edit_message_text(
                    "Broadcast is no longer pending."
                )

                return

            await query.edit_message_text(
                "Sending broadcast..."
            )

            user_ids = db.all_user_ids()

            sent, failed = await send_broadcast(
                context.bot,
                user_ids,
                broadcast["message"],
                logger,
            )

            db.complete_broadcast(
                broadcast_id,
                sent,
                failed,
            )

            await query.edit_message_text(
                "Broadcast complete.\n\n"
                f"Sent: {sent}\n"
                f"Failed: {failed}"
            )

            return

    ###########################################################
    # HOME
    ###########################################################

    if query.data == "home":

        await query.edit_message_text(
            text=welcome_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu(),
            disable_web_page_preview=True,
        )

        return

    ###########################################################
    # HELP
    ###########################################################

    if query.data == "help":

        await query.edit_message_text(
            text=help_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=back_menu(),
            disable_web_page_preview=True,
        )

        return

    ###########################################################
    # PUBLISHERS
    ###########################################################

    if query.data == "publishers":

        await query.edit_message_text(
            text=publishers_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=back_menu(),
            disable_web_page_preview=True,
        )

        return

    ###########################################################
    # SPONSOR
    ###########################################################

    if query.data == "sponsor":

        await query.edit_message_text(
            text=sponsor_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=back_menu(),
            disable_web_page_preview=True,
        )

        return

    ###########################################################
    # ABOUT
    ###########################################################

    if query.data == "about":

        await query.edit_message_text(
            text=about_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=back_menu(),
            disable_web_page_preview=True,
        )

        return
