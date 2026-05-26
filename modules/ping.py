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
from utils.i18n import Translator


strings = {
    "ru": {
        "wait": '<emoji id="6255963511252322252">✔️</emoji> понг..',
        "done": '<emoji id="6255963511252322252">✔️</emoji> понг.. ({ms} ms)',
        "inline.description": "Проверить работу inline",
        "inline.speed": "Скорость отклика: {ms} ms",
        "meta.description": "Проверка задержки соединения",
        "help.ping": "проверить скорость отклика Telegram.",
    },
    "en": {
        "wait": '<emoji id="6255963511252322252">✔️</emoji> pong..',
        "done": '<emoji id="6255963511252322252">✔️</emoji> pong.. ({ms} ms)',
        "inline.description": "Check inline response",
        "inline.speed": "Response speed: {ms} ms",
        "meta.description": "Connection latency check",
        "help.ping": "check Telegram response speed.",
    },
}

tr = Translator("ping", strings)


@Client.on_message(filters.command("ping", prefix) & filters.me)
async def ping(_, message: Message):
    t1 = time()

    await message.edit(tr("wait"))

    t2 = time()

    await message.edit(tr("done", ms=round((t2 - t1) * 1000)))


@inline_command("ping", tr("inline.description"))
async def inline_ping(app, query, args):
    t1 = time()

    me = await app.get_me()

    ping_ms = round((time() - t1) * 1000)

    return [
        InlineQueryResultArticle(
            title="🏓 Ping",
            description=tr("inline.speed", ms=ping_ms),
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
        "description": tr("meta.description"),
        "pic": "https://i.ibb.co/DfPSLWZ9/ping.png",
    },
    "ping": tr("help.ping"),
}
