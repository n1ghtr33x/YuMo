# -*- coding: utf-8 -*-

from html import escape

from pyrogram import Client, filters, errors
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from utils.i18n import Translator
from utils.inline import inline_command
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
        "page": "Страница",
        "no_description": "Без описания",
        "not_found": "<b>Не нашел модуль или команду:</b> <code>{name}</code>",
        "no_bot": "<b>Inline-бот не запущен.</b>\nДобавь <code>bot_token</code> в конфиг, чтобы inline-help работал.",
        "inline_error": "<b>Не удалось открыть inline-help:</b> <code>{error}</code>",
        "inline_empty": "<b>Inline-бот не вернул help-меню.</b>",
        "owner_only": "Эта справка не для тебя.",
        "btn.back": "Назад",
        "btn.modules": "Модули",
        "btn.prev": "Назад",
        "btn.next": "Дальше",
        "meta.description": "Inline-справочник по модулям",
        "help.help": "открыть inline-справочник по модулям или командам.",
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
        "page": "Page",
        "no_description": "No description",
        "not_found": "<b>Module or command not found:</b> <code>{name}</code>",
        "no_bot": "<b>Inline bot is not running.</b>\nAdd <code>bot_token</code> to config to use inline help.",
        "inline_error": "<b>Failed to open inline help:</b> <code>{error}</code>",
        "inline_empty": "<b>Inline bot did not return the help menu.</b>",
        "owner_only": "This help panel is not yours.",
        "btn.back": "Back",
        "btn.modules": "Modules",
        "btn.prev": "Prev",
        "btn.next": "Next",
        "meta.description": "Inline module help browser",
        "help.help": "open inline help for modules or commands.",
    },
}

tr = Translator("help", strings)

TOP = "╭─────────────────────"
MID = "├─────────────────────"
BOT = "╰─────────────────────"
ITEM = "│"
BRANCH = "╰─"
PAGE_SIZE = 6
_handlers_registered = False
_owner_id = None


def _commands(module_data: dict) -> dict:
    return {
        command: description
        for command, description in module_data.items()
        if command != "__meta__"
    }


def _module_names() -> list[str]:
    return sorted(modules_help)


def _page_count() -> int:
    names = _module_names()
    return max(1, (len(names) + PAGE_SIZE - 1) // PAGE_SIZE)


def _normalize_page(page: int) -> int:
    return max(0, min(page, _page_count() - 1))


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


def _module_for_query(query: str):
    if query in modules_help:
        return query, None, None

    for module_name, module_data in modules_help.items():
        for command, description in _commands(module_data).items():
            if query in _command_names(command):
                return module_name, command, description

    return None, None, None


def _format_index(page: int = 0) -> str:
    page = _normalize_page(page)
    names = _module_names()
    start = page * PAGE_SIZE
    shown = names[start:start + PAGE_SIZE]
    text = (
        f"{TOP}\n"
        f"{ITEM} <b>{tr('brand')}</b> · <i>{tr('title')}</i>\n"
        f"{ITEM} {tr('stats', count=len(modules_help), commands=_command_count())}\n"
        f"{ITEM} {tr('page')}: <code>{page + 1}/{_page_count()}</code>\n"
        f"{MID}\n"
        f"{ITEM} {tr('usage', prefix=prefix)}\n"
        f"{BOT}\n\n"
    )

    for module_name in shown:
        command_list = "  ".join(
            _command_chip(command)
            for command in _commands(modules_help[module_name])
        )
        text += f"<b>{module_name.title()}</b>\n{BRANCH} {command_list}\n\n"

    return text.rstrip()


def _format_module_help(module_name: str) -> str:
    module = modules_help[module_name]
    meta = module.get("__meta__", {})
    text = (
        f"{TOP}\n"
        f"{ITEM} <b>{tr('module_title')}</b> · <code>{module_name}</code>\n"
        f"{ITEM} <b>{tr('version')}:</b> <code>{meta.get('version', 'unknown')}</code>\n"
        f"{ITEM} <b>{tr('description')}:</b> <i>{meta.get('description', tr('no_description'))}</i>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('commands')}</b>\n"
    )

    for command, description in _commands(module).items():
        args = f" <code>{_command_args(command)}</code>" if _command_args(command) else ""
        text += (
            f"{ITEM}\n"
            f"{ITEM} {_command_chip(command)}{args}\n"
            f"{BRANCH} <i>{description}</i>\n"
        )

    return text + BOT


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


def _not_found(query: str) -> str:
    return f"{tr('not_found', name=escape(query))}\n\n<code>{prefix}help</code>"


def _index_markup(page: int = 0) -> InlineKeyboardMarkup:
    page = _normalize_page(page)
    names = _module_names()
    start = page * PAGE_SIZE
    shown = names[start:start + PAGE_SIZE]
    rows = [
        [InlineKeyboardButton(name.title(), callback_data=f"help:module:{name}")]
        for name in shown
    ]

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(tr("btn.prev"), callback_data=f"help:page:{page - 1}"))
    if page + 1 < _page_count():
        nav.append(InlineKeyboardButton(tr("btn.next"), callback_data=f"help:page:{page + 1}"))
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(rows)


def _back_markup(page: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(tr("btn.back"), callback_data=f"help:page:{_normalize_page(page)}")]]
    )


async def _edit_inline_or_message(client: Client, callback, text: str, markup=None) -> None:
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=markup,
            disable_web_page_preview=True,
        )
        return

    await client.edit_inline_text(
        callback.inline_message_id,
        text,
        reply_markup=markup,
        disable_web_page_preview=True,
    )


def _register_help_handlers(app: Client, owner_id: int) -> bool:
    global _handlers_registered, _owner_id

    bot = getattr(app, "bot", None)
    if not bot:
        return False

    _owner_id = owner_id

    if _handlers_registered:
        return True

    _handlers_registered = True

    @bot.on_callback_query(filters.regex(r"^help:"))
    async def help_callback(client, callback):
        if _owner_id and callback.from_user.id != _owner_id:
            await callback.answer(tr("owner_only"), show_alert=True)
            return

        try:
            _, action, value = callback.data.split(":", 2)

            if action == "page":
                page = _normalize_page(int(value))
                await _edit_inline_or_message(
                    client,
                    callback,
                    _format_index(page),
                    _index_markup(page),
                )
                await callback.answer()
                return

            if action == "module" and value in modules_help:
                await _edit_inline_or_message(
                    client,
                    callback,
                    _format_module_help(value),
                    _back_markup(),
                )
                await callback.answer()
                return

            await callback.answer(tr("not_found", name=value), show_alert=True)

        except errors.MessageNotModified:
            await callback.answer()
        except Exception as e:
            await callback.answer(str(e), show_alert=True)

    return True


@inline_command("help", tr("meta.description"))
async def inline_help(app: Client, query, args):
    _register_help_handlers(app, query.from_user.id)
    query_text = args.strip().lower()

    if not query_text:
        return [
            InlineQueryResultArticle(
                title=tr("brand"),
                description=tr("title"),
                input_message_content=InputTextMessageContent(_format_index()),
                reply_markup=_index_markup(),
            )
        ]

    module_name, command, description = _module_for_query(query_text)
    if module_name and command:
        text = _format_command_help(module_name, command, description)
    elif module_name:
        text = _format_module_help(module_name)
    else:
        text = _not_found(query_text)

    return [
        InlineQueryResultArticle(
            title=f"{tr('brand')}: {query_text}",
            description=tr("meta.description"),
            input_message_content=InputTextMessageContent(text),
            reply_markup=_back_markup(),
        )
    ]


@Client.on_message(filters.command(["help", "h"], prefix) & filters.me)
async def help_cmd(client: Client, message: Message):
    if not _register_help_handlers(client, message.from_user.id):
        await message.edit(tr("no_bot"))
        return

    query = "help"
    if len(message.command) > 1:
        query += " " + message.command[1].lower()

    try:
        bot_me = await client.bot.get_me()
        results = await client.get_inline_bot_results(bot_me.username, query)

        if not results.results:
            await message.edit(tr("inline_empty"))
            return

        await client.send_inline_bot_result(
            message.chat.id,
            results.query_id,
            results.results[0].id,
            reply_to_message_id=message.reply_to_message_id,
        )
        await message.delete()
    except Exception as e:
        await message.edit(tr("inline_error", error=escape(str(e))))


modules_help["help"] = {
    "__meta__": {
        "version": "2.0.0",
        "description": tr.lazy("meta.description"),
        "pic": "https://i.ibb.co/4ZfyNcL6/help.png",
    },
    "help [module/command]": tr.lazy("help.help"),
}
