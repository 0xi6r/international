from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from .ui import (
    about_text,
    back_menu,
    help_text,
    main_menu,
    publishers_text,
    sponsor_text,
    welcome_text,
)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

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
