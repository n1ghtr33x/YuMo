from pyrogram import Client, filters, types
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.db import db

aur_info = db.get(
    "core.aur",
    "message",
    {
        "message": 'None',
        "is_aur": False,
    },
)


@Client.on_message((filters.private | filters.mentioned)
                   & ~filters.channel
                   & ~filters.me
                   & ~filters.bot
                   )
async def aur_handler(_, message: types.Message):
    if db.get('core.aur', 'is_aur'):
        await message.reply(
            f"<b>{db.get('core.aur', 'message')}</b>"
        )


@Client.on_message(filters.command(["aur", 'autoresponder'], prefix) & filters.me)
async def aur(_, message: Message):
    if len(message.text.split(' ')) >= 2:
        mess = message.text.split(" ")[1:]
        messa = ' '.join(mess)
        await message.edit('<b>Автоответчик включен.</b>')
        db.set("core.aur", "is_aur", True)
        db.set('core.aur', 'message', messa)


@Client.on_message(filters.command(["unaur", 'autoresponder'], prefix) & filters.me)
async def unaur(_, message: Message):
    if db.get('core.aur', 'is_aur'):
        await message.edit('<b>Автоответчик отключен.</b>')
        db.set('core.aur', 'is_aur', False)
    else:
        await message.edit("<b>Автоответчик не был включен</b>")

    db.set("core.aur", "message", 'None')


modules_help["autoresponder"] = {"autoresponder [сообщение]": "включить автоответчик", "unautoresponder": "отключить автоответчик"}
