# -*- coding: utf-8 -*-

from time import time

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from utils.misc import modules_help, prefix
from utils.inline import inline_command
from utils.i18n import t


@Client.on_message(filters.command("ping", prefix) & filters.me)
async def ping(_, message: Message):
    t1 = time()

    await message.edit(t("ping.wait"))

    t2 = time()

    await message.edit(t("ping.done", ms=round((t2 - t1) * 1000)))


@inline_command("ping", t("ping.inline.description"))
async def inline_ping(app, query, args):
    t1 = time()

    me = await app.get_me()

    ping_ms = round((time() - t1) * 1000)

    return [
        InlineQueryResultArticle(
            title="🏓 Ping",
            description=f"Скорость отклика: {ping_ms} ms",
            input_message_content=InputTextMessageContent(
                f"""
<emoji id="6255963511252322252">✔️</emoji> <b>Pong!</b>

👤 <b>User:</b> {me.first_name}
⚡ <b>Ping:</b> <code>{ping_ms} ms</code>
"""
            ),
        )
    ]

modules_help["ping"] = {
    "__meta__": {
        "version": "1.0.0",
        "description": t("ping.meta.description"),
        "pic": "https://i.ibb.co/DfPSLWZ9/ping.png",
    },
    "ping": t("ping.help.ping")
}