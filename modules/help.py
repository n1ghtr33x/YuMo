# -*- coding: utf-8 -*-

from pyrogram import Client, filters
from pyrogram.errors import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from pyrogram.types import Message

from utils.i18n import Translator
from utils.misc import modules_help, prefix


strings = {
    "ru": {
        "title": "<b>Справочник YuMo</b>",
        "subtitle": "Модулей: <code>{count}</code> | Команд: <code>{commands}</code>",
        "hint": "Подробнее: <code>{prefix}help [модуль]</code> или <code>{prefix}help [команда]</code>",
        "module_title": "<b>Модуль: <code>{module}</code></b>",
        "version": "Версия",
        "description": "Описание",
        "commands": "Команды",
        "no_description": "Без описания",
        "command_title": "<b>Команда: <code>{prefix}{command}</code></b>",
        "command_module": "Модуль",
        "not_found": "<b>Не нашел модуль или команду:</b> <code>{name}</code>",
        "meta.description": "Красивый справочник по модулям",
        "help.help": "показать общий список, помощь по модулю или команде.",
    },
    "en": {
        "title": "<b>YuMo Help Desk</b>",
        "subtitle": "Modules: <code>{count}</code> | Commands: <code>{commands}</code>",
        "hint": "More info: <code>{prefix}help [module]</code> or <code>{prefix}help [command]</code>",
        "module_title": "<b>Module: <code>{module}</code></b>",
        "version": "Version",
        "description": "Description",
        "commands": "Commands",
        "no_description": "No description",
        "command_title": "<b>Command: <code>{prefix}{command}</code></b>",
        "command_module": "Module",
        "not_found": "<b>Module or command not found:</b> <code>{name}</code>",
        "meta.description": "A nicer module help browser",
        "help.help": "show all modules, module help, or command help.",
    },
}

tr = Translator("help", strings)


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


def _command_chip(command: str) -> str:
    return "/".join(
        f"<code>{prefix}{name}</code>"
        for name in _command_names(command)
    )


def _format_index_header() -> str:
    return (
        f"{tr('title')}\n"
        f"{tr('subtitle', count=len(modules_help), commands=_command_count())}\n"
        f"{tr('hint', prefix=prefix)}\n\n"
    )


def _format_index_lines() -> list[str]:
    lines = []

    for module_name, module_data in sorted(modules_help.items()):
        commands = " ".join(
            _command_chip(command)
            for command in _commands(module_data)
        )
        lines.append(f"<b>{module_name.title()}</b> - {commands}")

    return lines


def _format_module_help(module_name: str) -> tuple[str, str | None]:
    module = modules_help[module_name]
    meta = module.get("__meta__", {})
    commands = _commands(module)

    text = (
        f"{tr('module_title', module=module_name.title())}\n"
        f"<b>{tr('version')}:</b> <code>{meta.get('version', 'unknown')}</code>\n"
        f"<b>{tr('description')}:</b> <i>{meta.get('description', tr('no_description'))}</i>\n\n"
        f"<b>{tr('commands')}:</b>\n"
    )

    for command, description in commands.items():
        parts = command.split(maxsplit=1)
        args = f" <code>{parts[1]}</code>" if len(parts) > 1 else ""
        text += f"\n{_command_chip(command)}{args} - <i>{description}</i>"

    return text, meta.get("pic")


def _format_command_help(module_name: str, command: str, description: str) -> str:
    parts = command.split(maxsplit=1)
    args = f" <code>{parts[1]}</code>" if len(parts) > 1 else ""

    return (
        f"{tr('command_title', prefix=prefix, command=parts[0])}\n"
        f"<b>{tr('command_module')}:</b> <code>{module_name}</code> "
        f"(<code>{prefix}help {module_name}</code>)\n\n"
        f"{_command_chip(command)}{args} - <i>{description}</i>"
    )


async def _send_index(message: Message) -> None:
    header = _format_index_header()
    text = header
    edited = False

    for line in _format_index_lines():
        chunk = f"{line}\n"

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

    await message.edit(tr("not_found", name=query))


modules_help["help"] = {
    "__meta__": {
        "version": "1.1.0",
        "description": tr.lazy("meta.description"),
        "pic": "https://i.ibb.co/4ZfyNcL6/help.png",
    },
    "help [module/command]": tr.lazy("help.help"),
}
