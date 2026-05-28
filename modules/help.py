# -*- coding: utf-8 -*-

from pyrogram import Client, filters
from pyrogram.errors import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from pyrogram.types import Message

from utils.i18n import Translator
from utils.misc import modules_help, prefix


strings = {
    "ru": {
        "brand": "YuMo Help",
        "title": "Справочник модулей",
        "stats": "Модулей: <code>{count}</code>  |  Команд: <code>{commands}</code>",
        "usage": "<code>{prefix}help [модуль]</code> или <code>{prefix}help [команда]</code>",
        "module_title": "Карточка модуля",
        "command_title": "Карточка команды",
        "version": "Версия",
        "description": "Описание",
        "commands": "Команды",
        "module": "Модуль",
        "aliases": "Алиасы",
        "usage_label": "Формат",
        "no_description": "Без описания",
        "not_found": "<b>Не нашел модуль или команду:</b> <code>{name}</code>\n<code>{prefix}help</code> покажет весь список.",
        "meta.description": "Оформленный справочник по модулям",
        "help.help": "показать красивый список модулей, помощь по модулю или команде.",
    },
    "en": {
        "brand": "YuMo Help",
        "title": "Module directory",
        "stats": "Modules: <code>{count}</code>  |  Commands: <code>{commands}</code>",
        "usage": "<code>{prefix}help [module]</code> or <code>{prefix}help [command]</code>",
        "module_title": "Module card",
        "command_title": "Command card",
        "version": "Version",
        "description": "Description",
        "commands": "Commands",
        "module": "Module",
        "aliases": "Aliases",
        "usage_label": "Usage",
        "no_description": "No description",
        "not_found": "<b>Module or command not found:</b> <code>{name}</code>\n<code>{prefix}help</code> shows the full list.",
        "meta.description": "A styled module help browser",
        "help.help": "show a styled module list, module help, or command help.",
    },
}

tr = Translator("help", strings)


TOP = "╭─────────────────────"
MID = "├─────────────────────"
BOT = "╰─────────────────────"
ITEM = "│"
BRANCH = "╰─"


def _commands(module_data: dict) -> dict:
    return {
        command: description
        for command, description in module_data.items()
        if command != "__meta__"
    }


def _command_count() -> int:
    return sum(len(_commands(module_data)) for module_data in modules_help.values())


def _command_names(command: str) -> list[str]:
    return command.split()[0].split("/")


def _command_args(command: str) -> str:
    parts = command.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else ""


def _command_chip(command: str) -> str:
    return " ".join(
        f"<code>{prefix}{name}</code>"
        for name in _command_names(command)
    )


def _format_index_header() -> str:
    return (
        f"{TOP}\n"
        f"{ITEM} <b>{tr('brand')}</b> · <i>{tr('title')}</i>\n"
        f"{ITEM} {tr('stats', count=len(modules_help), commands=_command_count())}\n"
        f"{MID}\n"
        f"{ITEM} {tr('usage', prefix=prefix)}\n"
        f"{BOT}\n\n"
    )


def _format_index_lines() -> list[str]:
    lines = []

    for module_name, module_data in sorted(modules_help.items()):
        commands = _commands(module_data)
        command_list = "  ".join(
            _command_chip(command)
            for command in commands
        )

        lines.append(
            f"<b>{module_name.title()}</b>\n"
            f"{BRANCH} {command_list}"
        )

    return lines


def _format_module_help(module_name: str) -> tuple[str, str | None]:
    module = modules_help[module_name]
    meta = module.get("__meta__", {})
    commands = _commands(module)

    text = (
        f"{TOP}\n"
        f"{ITEM} <b>{tr('module_title')}</b> · <code>{module_name}</code>\n"
        f"{ITEM} <b>{tr('version')}:</b> <code>{meta.get('version', 'unknown')}</code>\n"
        f"{ITEM} <b>{tr('description')}:</b> <i>{meta.get('description', tr('no_description'))}</i>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('commands')}</b>\n"
    )

    for command, description in commands.items():
        args = f" <code>{_command_args(command)}</code>" if _command_args(command) else ""
        text += (
            f"{ITEM}\n"
            f"{ITEM} {_command_chip(command)}{args}\n"
            f"{BRANCH} <i>{description}</i>\n"
        )

    text += BOT
    return text, meta.get("pic")


def _format_command_help(module_name: str, command: str, description: str) -> str:
    args = f" <code>{_command_args(command)}</code>" if _command_args(command) else ""

    return (
        f"{TOP}\n"
        f"{ITEM} <b>{tr('command_title')}</b>\n"
        f"{ITEM} <b>{tr('module')}:</b> <code>{module_name}</code>\n"
        f"{ITEM} <b>{tr('aliases')}:</b> {_command_chip(command)}\n"
        f"{ITEM} <b>{tr('usage_label')}:</b> {_command_chip(command)}{args}\n"
        f"{MID}\n"
        f"{ITEM} <i>{description}</i>\n"
        f"{BOT}\n\n"
        f"<code>{prefix}help {module_name}</code>"
    )


async def _send_index(message: Message) -> None:
    header = _format_index_header()
    text = header
    edited = False

    for line in _format_index_lines():
        chunk = f"{line}\n\n"

        if len(text) + len(chunk) >= 3900:
            if edited:
                await message.reply(text, disable_web_page_preview=True)
            else:
                await message.edit(text, disable_web_page_preview=True)
                edited = True

            text = header

        text += chunk

    if edited:
        await message.reply(text, disable_web_page_preview=True)
    else:
        await message.edit(text, disable_web_page_preview=True)


@Client.on_message(filters.command(["help", "h"], prefix) & filters.me)
async def help_cmd(_, message: Message):
    if len(message.command) == 1:
        await _send_index(message)
        return

    query = message.command[1].lower()

    if query in modules_help:
        text, pic = _format_module_help(query)

        if pic and len(text) < 1024:
            try:
                await message.reply_photo(photo=pic, caption=text)
                await message.delete()
                return
            except (WebpageMediaEmpty, PhotoInvalidDimensions, MediaEmpty):
                pass

        await message.edit(text, disable_web_page_preview=True)
        return

    for module_name, module_data in modules_help.items():
        for command, description in _commands(module_data).items():
            if query in _command_names(command):
                await message.edit(
                    _format_command_help(module_name, command, description),
                    disable_web_page_preview=True,
                )
                return

    await message.edit(tr("not_found", name=query, prefix=prefix))


modules_help["help"] = {
    "__meta__": {
        "version": "1.2.0",
        "description": tr.lazy("meta.description"),
        "pic": "https://i.ibb.co/4ZfyNcL6/help.png",
    },
    "help [module/command]": tr.lazy("help.help"),
}
