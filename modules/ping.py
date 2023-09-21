from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from time import time


@Client.on_message(filters.command("ping", prefix) & filters.me)
async def ping(_, message: Message):
    t1 = time()
    await message.edit('Понг')
    t2 = time()
    await message.edit(f'Понг.. (0.{int((t2-t1)*1000)} ms)')

modules_help['ping'] = {
    'ping': 'проверить скорость отклика Telegram.'
}
