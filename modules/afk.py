import datetime

from pyrogram import Client, filters, types

from utils.misc import modules_help, prefix
from utils.db import db


afk_info = db.get(
    "afk",
    "afk_info",
    {
        "start": 0,
        "is_afk": False,
        "reason": "",
    },
)

is_afk = filters.create(lambda _, __, ___: afk_info["is_afk"])


@Client.on_message(
    is_afk
    & (filters.private | filters.mentioned)
    & ~filters.channel
    & ~filters.me
    & ~filters.bot
)
async def afk_handler(_, message: types.Message):
    start = datetime.datetime.fromtimestamp(afk_info["start"])
    end = datetime.datetime.now().replace(microsecond=0)
    afk_time = end - start
    await message.reply(
        f"<b>Я в афк.. (уже {afk_time})\n" f"Сообщение:</b> <i>{afk_info['reason']}</i>"
    )


@Client.on_message(filters.command("afk", prefix) & filters.me)
async def afk(_, message):
    if len(message.text.split()) >= 2:
        reason = message.text.split(" ", maxsplit=1)[1]
    else:
        reason = "None"

    afk_info["start"] = int(datetime.datetime.now().timestamp())
    afk_info["is_afk"] = True
    afk_info["reason"] = reason

    if reason != 'None':
        await message.edit(f"<b>Я вошел в режим афк.\n" f"Сообщение:</b> <i>{reason}</i>")
    else:
        await message.edit(f'<b>Я вошел в режим афк</b>')

    db.set("afk", "afk_info", afk_info)


@Client.on_message(filters.command("unafk", prefix) & filters.me)
async def unafk(_, message):
    if afk_info["is_afk"]:
        start = datetime.datetime.fromtimestamp(afk_info["start"])
        end = datetime.datetime.now().replace(microsecond=0)
        afk_time = end - start
        await message.edit(f"<b>Я больше не в афк.\n" f"Я был в афк {afk_time}</b>")
        afk_info["is_afk"] = False
    else:
        await message.edit("<b>Ты не в афк.</b>")

    db.set("afk", "afk_info", afk_info)


modules_help["afk"] = {"afk [сообщение]": "Войти в афк", "unafk": "Выйти из афк"}
