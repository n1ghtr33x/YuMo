from pyrogram import Client, filters
from pyrogram.types import Message

from utils.db import db
from utils.misc import modules_help, prefix
from asyncio import sleep


ModuleName = 'core.spam'


@Client.on_message(filters.command('spam', prefix) & filters.me)
async def spam(client: Client, message: Message):
    if len(message.text.split(' ')) >= 3:
        text = message.text.split(' ')
        delay = text[1]
        spam_text = text[2:]
        db.set(ModuleName, 'state', True)
        await message.edit(f'<b>Спам запущен!\nЗадержка: {delay}</b>')
        while db.get(ModuleName, 'state'):
            await client.send_message(message.chat.id, f' '.join(spam_text))
            await sleep(float(delay))


@Client.on_message(filters.command('spam_off', prefix) & filters.me)
async def spam_off(_, message: Message):
    await message.edit('<b>Спам остановлен!</b>')
    db.set(ModuleName, 'state', False)


modules_help['spam'] = {
    'spam [delay] [text]': 'запустить спам',
    'spam_off': 'выключить спам'
}
