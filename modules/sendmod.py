import os

from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import (
    format_exc,
    format_module_help,
    format_small_module_help,
)


@Client.on_message(filters.command(["sendmod", "sm"], prefix) & filters.me)
async def sendmod(client: Client, message: Message):
    if len(message.command) == 1:
        await message.edit("<b>Пожалуйста воодите имя модуля!</b>")
        return

    await message.edit("<b>Загрузка...</b>")
    try:
        module_name = message.command[1].lower()
        if module_name in modules_help:
            text = format_module_help(module_name)
            if len(text) >= 1024:
                text = format_small_module_help(module_name)
            if os.path.isfile(f"modules/{module_name}.py"):
                await client.send_document(
                    message.chat.id, f"modules/{module_name}.py", caption=text
                )
            elif os.path.isfile(
                f"modules/custom_modules/{module_name.lower()}.py"
            ):
                await client.send_document(
                    message.chat.id,
                    f"modules/custom_modules/{module_name}.py",
                    caption=text,
                )
            await message.delete()
        else:
            await message.edit(f"<b>Модуль {module_name} не найден!</b>")
    except Exception as e:
        await message.edit(format_exc(e))


modules_help["sendmod"] = {
    "sendmod [module_name]": "отправить модуль в чат.",
}
