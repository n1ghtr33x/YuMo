# -*- coding: utf-8 -*-

import os
import platform

from pyrogram import Client, filters
from pyrogram.types import Message

from utils.i18n import Translator
from utils.misc import modules_help, prefix, python_version, userbot_version


strings = {
    "ru": {
        "title": "YuMo UserBot",
        "subtitle": "Информация о системе",
        "version": "Версия YuMo",
        "prefix": "Префикс",
        "python": "Python",
        "system": "Система",
        "machine": "Архитектура",
        "cpu": "CPU ядер",
        "links": "Ссылки",
        "channel": "Канал",
        "developer": "Разработчик",
        "meta.description": "Информация о юзерботе и системе",
        "help.info": "показать информацию о YuMo и системе.",
    },
    "en": {
        "title": "YuMo UserBot",
        "subtitle": "System information",
        "version": "YuMo version",
        "prefix": "Prefix",
        "python": "Python",
        "system": "System",
        "machine": "Architecture",
        "cpu": "CPU cores",
        "links": "Links",
        "channel": "Channel",
        "developer": "Developer",
        "meta.description": "Userbot and system information",
        "help.info": "show YuMo and system information.",
    },
}

tr = Translator("info", strings)

TOP = "╭─────────────────────"
MID = "├─────────────────────"
BOT = "╰─────────────────────"
ITEM = "│"

CHANNEL_URL = "https://t.me/n1ghtr33x_channel"
DEVELOPER_URL = "https://t.me/d08ee"


def _format_info() -> str:
    system = platform.uname()

    return (
        f"{TOP}\n"
        f"{ITEM} <b>{tr('title')}</b> · <i>{tr('subtitle')}</i>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('version')}:</b> <code>{userbot_version}</code>\n"
        f"{ITEM} <b>{tr('prefix')}:</b> <code>{prefix}</code>\n"
        f"{ITEM} <b>{tr('python')}:</b> <code>{python_version}</code>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('system')}:</b> <code>{system.system} {system.release}</code>\n"
        f"{ITEM} <b>{tr('machine')}:</b> <code>{system.machine}</code>\n"
        f"{ITEM} <b>{tr('cpu')}:</b> <code>{os.cpu_count()}</code>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('links')}</b>\n"
        f"{ITEM} <b>{tr('channel')}:</b> <a href='{CHANNEL_URL}'>YuMo</a>\n"
        f"{ITEM} <b>{tr('developer')}:</b> <a href='{DEVELOPER_URL}'>Чайна</a>\n"
        f"{BOT}"
    )


@Client.on_message(filters.command("info", prefix) & filters.me)
async def info(_, message: Message):
    await message.edit(_format_info(), disable_web_page_preview=True)


modules_help["info"] = {
    "__meta__": {
        "version": "1.1.0",
        "description": tr.lazy("meta.description"),
        "pic": "https://i.ibb.co/4ZfyNcL6/help.png",
    },
    "info": tr.lazy("help.info"),
}
