import logging

from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent

inline_handlers = {}
INLINE_OWNER_ID = None


def inline_command(name: str, description: str = ""):
    def decorator(func):
        inline_handlers[name] = {
            "func": func,
            "description": description,
        }
        return func

    return decorator


async def setup_inline(app, bot):
    if not bot:
        logging.warning("Inline bot is not started")
        return
    me = await app.get_me()
    global INLINE_OWNER_ID
    INLINE_OWNER_ID = me.id

    @bot.on_inline_query()
    async def inline_query_handler(client, query):
        if query.from_user.id != INLINE_OWNER_ID:
            await query.answer(
                [],
                cache_time=60,
                is_personal=True,
                switch_pm_text="⛔ Inline недоступен",
                switch_pm_parameter="denied",
            )
            return
        text = query.query.strip()

        if not text:
            results = [
                InlineQueryResultArticle(
                    title=name,
                    description=data["description"],
                    input_message_content=InputTextMessageContent(
                        f"<b>Inline command:</b> <code>{name}</code>"
                    ),
                )
                for name, data in inline_handlers.items()
            ]

            await query.answer(results, cache_time=1, is_personal=True)
            return

        command, *args = text.split(maxsplit=1)
        args = args[0] if args else ""

        handler = inline_handlers.get(command)

        if not handler:
            await query.answer([], cache_time=1, is_personal=True)
            return

        try:
            results = await handler["func"](app, query, args)

            if results is None:
                results = []

            await query.answer(results, cache_time=1, is_personal=True)

        except Exception as e:
            logging.exception("Inline handler error")

            await query.answer(
                [
                    InlineQueryResultArticle(
                        title="Ошибка",
                        description=str(e),
                        input_message_content=InputTextMessageContent(
                            f"<b>Inline error:</b>\n<code>{e}</code>"
                        ),
                    )
                ],
                cache_time=1,
                is_personal=True,
            )