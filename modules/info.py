from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix, userbot_version, python_version
import platform
import os


my_system = platform.uname()


@Client.on_message(filters.command('info', prefix) & filters.me)
async def info(_, message: Message):
    await message.edit("<emoji id='5435965782414602696'>🕊</emoji>"
                       "<a href=https://t.me/irisobote>-YuMo UserBot-</a>"
                       "<emoji id='5435965782414602696'>🕊</emoji>\n\n"
                       f"<b>| Версия [{userbot_version}]\n"
                       f"| Префикс [ {prefix} ]\n"
                       f"| Канал юзербота <a href='t.me/irisobote'>{'{клик}'}</a>\n"
                       f"| Разработчик <a href='t.me/d08ee'>Чайна</a>\n"
                       f"| Версия Python: {python_version}\n"
                       f"| Система: {my_system.system}\n"
                       f"| Количество ядер CPU: {os.cpu_count()}</b>", disable_web_page_preview=True)

modules_help['info'] = {
    'info': 'иформация о юзерботе'
}
