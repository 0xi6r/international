import logging

BROADCAST_PREFIX = "📢 Bot Update\n\n"
BROADCAST_LIMIT = 4096 - len(BROADCAST_PREFIX)


async def send_broadcast(bot, user_ids, payload: str, logger: logging.Logger):

    sent = 0
    failed = 0
    text = BROADCAST_PREFIX + payload

    for telegram_id in user_ids:

        try:

            await bot.send_message(
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

    return sent, failed
