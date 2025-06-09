from pyrogram import Client, filters
from pyrogram.types import Message

from utils.db import db
from utils.scripts import restart
from utils.misc import modules_help, prefix


@Client.on_message(
    filters.command(["sp", "setprefix", "setprefix_yumo"], prefix)
    & filters.me
)
async def setprefix(_, message: Message):
    if len(message.command) > 1:
        pref = message.command[1]
        if len(pref) == 1:
            db.set("core.main", "prefix", pref)
            await message.edit(f"<b>Префикс [ <code>{pref}</code> ] установлен!</b>")
            restart()
        else:
            await message.edit(f'Префикс должен содержать один символ!')
    else:
        await message.edit("<b>Префикс не может быть пустой!</b>")


@Client.on_message(filters.command('prefix', prefix) & filters.me)
async def prefix(_, message: Message):
    await message.edit(f'Текущий префикс [ <code>{db.get("core.main", "prefix", ".")}<code> ]')


modules_help["prefix"] = {
    "setprefix [prefix]": "установить свой префикс.",
    "prefix": "посмотреть префикс",
}
