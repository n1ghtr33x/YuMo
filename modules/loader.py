import os

from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.db import db
from utils.scripts import unload_module, format_exc, load_module, restart

BASE_PATH = os.path.abspath(os.getcwd())


@Client.on_message(filters.command(["loadmod", "lm"], prefix) & filters.me)
async def loadmod(client: Client, message: Message):
    db.set(
        "core.updater",
        "restart_info",
        {
            "type": "loadmodule",
            "chat_id": message.chat.id,
            "message_id": message.id,
        },
    )

    if message.reply_to_message:
        if message.reply_to_message.document and message.reply_to_message.document.file_name.split('.')[1] == 'py':
            await message.edit('Скачивание модуля...')
            await client.download_media(message.reply_to_message.document.file_id,
                                        f'modules/custom_modules/{message.reply_to_message.document.file_name}')
            await message.edit("<b>Загрузка модуля... (5 sec.)</b>")
            await load_module(f'{message.reply_to_message.document.file_name.replace(".py", "")}', client)
            await message.edit("Модуль загружен!")
            restart()
        else:
            await message.edit("Это не модуль!")
    else:
        await message.edit('А что загружать то?..')


@Client.on_message(filters.command(["unloadmod", "ulm"], prefix) & filters.me)
async def unload_mods(client: Client, message: Message):
    if len(message.command) <= 1:
        return await message.edit("<b>Specify module to unload</b>")

    module_name = message.command[1].lower()

    if os.path.exists(f"{BASE_PATH}/modules/custom_modules/{module_name}.py"):
        try:
            await unload_module(module_name, client)
        except Exception as e:
            return await message.edit(format_exc(e))

        os.remove(f"{BASE_PATH}/modules/custom_modules/{module_name}.py")
        await message.edit(
            f"<b>Модуль <code>{module_name}</code> выгружен и удален!</b>")


@Client.on_message(filters.command('del_all', prefix) & filters.me)
async def del_all(_, message: Message):
    files = os.listdir('modules/custom_modules')
    if files:
        for i in files:
            os.remove(f'modules/custom_modules/{i}')
    await message.edit('Все модули успешно удалены!')
    restart()


modules_help['loader'] = {
    'loadmod [реплай на модуль]': 'загрузить модуль из файла',
    'unloadmod [название модуля]': 'выгрузить и удалить модуль',
    'del_all': 'удалить все кастомные модули'
}
