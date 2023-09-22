from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.db import db

from asyncio import sleep

gram = 5788046441
ModuleName = 'gram_mod'


@Client.on_message(filters.bot & filters.private)
async def get_info(client: Client, message: Message):
    me = await client.get_me()
    if message.from_user.id == me.id:
        if message.text == '👤 Профиль':
            await message.delete()

    if message.from_user.id == gram:
        slash = '\n'
        if message.text.split(slash)[0] == 'Профиль':
            db.set(ModuleName, 'info', message.text.split(slash))
            data = db.get(ModuleName, 'info')
            grams = data[2].split('|')[0].split(' ')[2]
            galeons = data[2].split('|')[1].split(' ')[2]
            await message.delete()
            info_chat = db.get(ModuleName, 'info_chat')
            info_message_id = db.get(ModuleName, 'info_message_id')
            info_from_user_id = db.get(ModuleName, 'info_from_user_id')
            is_photo = db.get(ModuleName, 'is_photo')
            first_name = db.get(ModuleName, 'info_first_name')
            user_name = db.get(ModuleName, 'info_username')
            if is_photo:
                await client.send_photo(info_chat, f'photos/{info_from_user_id}.png',
                                        caption=f'[⏹️] Gram Help [⏹️]\n\n'
                                                f'[⏹️] <code>.ghelp</code> - открыть хелп меню[⏹️]\n'
                                                f'[⏹️] <code>.gram_on</code> [задержка в минутах] - запустить фарм\n'
                                                f'[⏹️] <code>.gram_off</code> - остановить фарм[⏹️]\n\n'

                                                f'[⏹️] Грамы: {grams} [⏹️]\n'
                                                f'[⏹️] Галеоны: {galeons} [⏹️]\n\n'

                                                f'[⏹️] Имя: <code>{first_name}</code> [⏹️]\n'
                                                f'[⏹️] Никнейм: <code>{user_name}</code> [⏹️]\n'
                                                f'[⏹️] Id: <code>{info_from_user_id}</code> [⏹️]\n')
                await client.delete_messages(info_chat, info_message_id)
            else:
                await client.edit_message_text(info_chat, info_message_id, f'[⏹️] Gram Help [⏹️]\n\n'
                                                                           f'[⏹️] <code>.ghelp</code> - открыть хелп меню[⏹️]\n'
                                                                           f'[⏹️] <code>.gram_on</code> [задержка в минутах] - запустить фарм\n'
                                                                           f'[⏹️] <code>.gram_off</code> - остановить фарм[⏹️]\n\n'

                                                                           f'[⏹️] Грамы: {grams} [⏹️]\n'
                                                                           f'[⏹️] Галеоны: {galeons} [⏹️]\n\n'

                                                                           f'[⏹️] Имя: <code>{first_name}</code> [⏹️]\n'
                                                                           f'[⏹️] Никнейм: <code>{user_name}</code> [⏹️]\n'
                                                                           f'[⏹️] Id: <code>{info_from_user_id}</code> [⏹️]\n')

    if db.get(ModuleName, 'farm'):
        if message.text == 'Хогвартс':
            if message.reply_markup:
                for i in message.reply_markup.inline_keyboard:
                    if i[0].text == 'Дуэли':
                        await client.request_callback_answer(message.chat.id, message.id, i[0].callback_data)


@Client.on_edited_message(filters.bot & filters.private)
async def edited_message(client: Client, message: Message):
    message_id = message.id
    chat_id = message.chat.id
    text = message.text
    if db.get(ModuleName, 'farm'):
        if text == 'Хогвартс':
            if message.reply_markup:
                for i in message.reply_markup.inline_keyboard:
                    if i[0].text == '⚔️ В бой':
                        await client.request_callback_answer(chat_id, message_id, i[0].callback_data)
        if message.text.split(' ')[0] == 'Ваши':
            if message.reply_markup:
                for i in message.reply_markup.inline_keyboard:
                    if i[0].text == '⚔️ Атаковать':
                        await client.request_callback_answer(chat_id, message_id, i[0].callback_data)


@Client.on_message(filters.command("ghelp", prefix) & filters.me)
async def lm(client: Client, message: Message):
    await message.edit('Загрузка..')
    db.set(ModuleName, 'info_chat', message.chat.id)
    db.set(ModuleName, 'info_message_id', message.id)
    db.set(ModuleName, 'info_from_user_id', message.from_user.id)
    db.set(ModuleName, 'info_first_name', message.from_user.first_name)
    db.set(ModuleName, 'info_username', message.from_user.username)

    if message.from_user.photo:
        await client.download_media(message.from_user.photo.big_file_id, f'photos/{message.from_user.id}.png')
        db.set(ModuleName, 'is_photo', True)
    else:
        db.set(ModuleName, 'is_photo', False)
    await client.send_message(gram, '👤 Профиль')


@Client.on_message(filters.command("gram_on", prefix) & filters.me)
async def gram_on(client: Client, message: Message):
    db.set(ModuleName, 'farm', True)
    if len(message.text.split(' ')) == 2:
        time = message.text.split(' ')[1]
        try:
            a = int(time) + 1
            time = int(time)
            while db.get(ModuleName, 'farm'):
                a = await client.send_message(gram, '🔮 Хогвартс')
                await message.edit(f'Фарм запущен!\nИнтервал: {time}')
                await sleep(0.5)
                await a.delete()
                await sleep(time * 60)
        except ValueError:
            await message.edit('Вводите число в минутах.')
    else:
        while db.get(ModuleName, 'farm'):
            await message.edit('Фарм запущен!\nИнтервал: 10 мин')
            a = await client.send_message(gram, '🔮 Хогвартс')
            await sleep(0.5)
            await a.delete()
            await sleep(700)


@Client.on_message(filters.command('gram_off', prefix) & filters.me)
async def gram_off(client: Client, message: Message):
    db.set(ModuleName, 'farm', False)
    await message.edit('Фарм остановлен!')


modules_help["gram_mod"] = {
    "ghelp": "хелп меню",
    'gram_on [задержка в минутах]': 'запустить фарм',
    'gram_off': 'остановить фарм'
}
