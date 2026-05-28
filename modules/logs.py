# -*- coding: utf-8 -*-

from html import escape
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message

from utils.i18n import Translator
from utils.misc import modules_help, prefix

strings = {
    "ru": {
        "missing": "<b>Лог-файл пока не найден.</b>",
        "title": "Последние строки лога",
        "sent": "<b>Лог отправлен файлом.</b>",
        "meta.description": "Просмотр последних логов YuMo",
        "help.logs": "показать последние строки лога или отправить лог файлом.",
    },
    "en": {
        "missing": "<b>Log file is not found yet.</b>",
        "title": "Latest log lines",
        "sent": "<b>Log sent as file.</b>",
        "meta.description": "View latest YuMo logs",
        "help.logs": "show latest log lines or send log file.",
    },
}

tr = Translator("logs", strings)
LOG_PATH = Path("yumo.log")


@Client.on_message(filters.command("logs", prefix) & filters.me)
async def logs_cmd(client: Client, message: Message):
    if not LOG_PATH.exists():
        await message.edit(tr("missing"))
        return

    if len(message.command) > 1 and message.command[1].lower() in {"file", "f"}:
        await client.send_document(message.chat.id, str(LOG_PATH), caption=tr("title"))
        await message.delete()
        return

    lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
    text = "\n".join(lines)[-3500:] or "empty"
    await message.edit(f"<b>{tr('title')}:</b>\n<code>{escape(text)}</code>")


modules_help["logs"] = {
    "__meta__": {"version": "1.0.0", "description": tr.lazy("meta.description")},
    "logs [file]": tr.lazy("help.logs"),
}
