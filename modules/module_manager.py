# -*- coding: utf-8 -*-

import os
from html import escape
from pathlib import Path

from pyrogram import Client, filters, errors
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from utils.db import db
from utils.i18n import Translator
from utils.inline import inline_command
from utils.misc import modules_help, prefix
from utils.scripts import restart


strings = {
    "ru": {
        "title": "Менеджер модулей",
        "subtitle": "inline-панель управления",
        "modules": "Модулей",
        "custom": "Кастомных",
        "core": "Системных",
        "page": "Страница",
        "commands": "Команды",
        "version": "Версия",
        "description": "Описание",
        "file": "Файл",
        "type": "Тип",
        "status": "Статус",
        "enabled": "включен",
        "disabled": "выключен",
        "protected": "защищен",
        "type.core": "core",
        "type.custom": "custom",
        "not_found": "Модуль не найден: {module}",
        "no_bot": "<b>Inline-бот не запущен.</b>\nДобавь <code>bot_token</code> в конфиг, чтобы module manager работал.",
        "inline_error": "<b>Не удалось открыть менеджер:</b> <code>{error}</code>",
        "inline_empty": "<b>Inline-бот не вернул менеджер модулей.</b>",
        "owner_only": "Этот менеджер не для тебя.",
        "enabled_alert": "Модуль {module} включен. Перезапускаюсь...",
        "disabled_alert": "Модуль {module} выключен. Перезапускаюсь...",
        "protected_alert": "Этот модуль нельзя выключить из менеджера.",
        "restarting": "Перезапускаюсь...",
        "btn.back": "Назад",
        "btn.prev": "Назад",
        "btn.next": "Дальше",
        "btn.send": "Отправить модуль",
        "btn.enable": "Включить",
        "btn.disable": "Выключить",
        "meta.description": "Inline-менеджер модулей YuMo",
        "help.manager": "открыть inline-менеджер модулей.",
    },
    "en": {
        "title": "Module Manager",
        "subtitle": "inline control panel",
        "modules": "Modules",
        "custom": "Custom",
        "core": "Core",
        "page": "Page",
        "commands": "Commands",
        "version": "Version",
        "description": "Description",
        "file": "File",
        "type": "Type",
        "status": "Status",
        "enabled": "enabled",
        "disabled": "disabled",
        "protected": "protected",
        "type.core": "core",
        "type.custom": "custom",
        "not_found": "Module not found: {module}",
        "no_bot": "<b>Inline bot is not running.</b>\nAdd <code>bot_token</code> to config to use module manager.",
        "inline_error": "<b>Failed to open manager:</b> <code>{error}</code>",
        "inline_empty": "<b>Inline bot did not return module manager.</b>",
        "owner_only": "This manager is not yours.",
        "enabled_alert": "Module {module} enabled. Restarting...",
        "disabled_alert": "Module {module} disabled. Restarting...",
        "protected_alert": "This module cannot be disabled from manager.",
        "restarting": "Restarting...",
        "btn.back": "Back",
        "btn.prev": "Prev",
        "btn.next": "Next",
        "btn.send": "Send module",
        "btn.enable": "Enable",
        "btn.disable": "Disable",
        "meta.description": "Inline YuMo module manager",
        "help.manager": "open the inline module manager.",
    },
}

tr = Translator("module_manager", strings)

TOP = "╭─────────────────────"
MID = "├─────────────────────"
BOT = "╰─────────────────────"
ITEM = "│"
BRANCH = "╰─"
PAGE_SIZE = 7
_handlers_registered = False
_owner_id = None


def _module_names() -> list[str]:
    names = set(modules_help)

    for path in Path("modules").rglob("*.py"):
        if path.stem != "__init__":
            names.add(path.stem)

    return sorted(names)


def _disabled_modules() -> set[str]:
    return set(db.get("core.modules", "disabled", []))


def _set_disabled_modules(disabled: set[str]) -> None:
    db.set("core.modules", "disabled", sorted(disabled))


def _is_disabled(module_name: str) -> bool:
    return module_name in _disabled_modules()


def _is_protected(module_name: str) -> bool:
    path = _module_path(module_name)
    return not path or "custom_modules" not in Path(path).parts


def _status(module_name: str) -> str:
    if _is_protected(module_name):
        return tr("protected")

    return tr("disabled") if _is_disabled(module_name) else tr("enabled")


def _module_path(module_name: str) -> str | None:
    for path in (
        f"modules/{module_name}.py",
        f"modules/custom_modules/{module_name}.py",
    ):
        if os.path.isfile(path):
            return path
    return None


def _is_custom(module_name: str) -> bool:
    path = _module_path(module_name)
    return bool(path and "custom_modules" in Path(path).parts)


def _custom_count() -> int:
    return sum(1 for name in _module_names() if _is_custom(name))


def _command_count(module_name: str) -> int:
    if module_name not in modules_help:
        return 0

    return len([key for key in modules_help[module_name] if key != "__meta__"])


def _page_count() -> int:
    names = _module_names()
    return max(1, (len(names) + PAGE_SIZE - 1) // PAGE_SIZE)


def _normalize_page(page: int) -> int:
    return max(0, min(page, _page_count() - 1))


def _format_index(page: int = 0) -> str:
    page = _normalize_page(page)
    names = _module_names()
    start = page * PAGE_SIZE
    shown = names[start:start + PAGE_SIZE]
    custom_count = _custom_count()

    text = (
        f"{TOP}\n"
        f"{ITEM} <b>{tr('title')}</b> · <i>{tr('subtitle')}</i>\n"
        f"{ITEM} <b>{tr('modules')}:</b> <code>{len(names)}</code>  "
        f"<b>{tr('core')}:</b> <code>{len(names) - custom_count}</code>  "
        f"<b>{tr('custom')}:</b> <code>{custom_count}</code>\n"
        f"{ITEM} <b>{tr('page')}:</b> <code>{page + 1}/{_page_count()}</code>\n"
        f"{MID}\n"
    )

    for module_name in shown:
        module_type = tr("type.custom") if _is_custom(module_name) else tr("type.core")
        text += (
            f"{ITEM} <b>{module_name}</b> "
            f"<code>{module_type}</code> · "
            f"{tr('status')}: <code>{_status(module_name)}</code> · "
            f"{tr('commands')}: <code>{_command_count(module_name)}</code>\n"
        )

    return text + BOT


def _format_module(module_name: str) -> str:
    if module_name not in modules_help and not _module_path(module_name):
        return f"<b>{tr('not_found', module=escape(module_name))}</b>"

    module = modules_help.get(module_name, {})
    meta = module.get("__meta__", {})
    module_path = _module_path(module_name) or "-"
    module_type = tr("type.custom") if _is_custom(module_name) else tr("type.core")
    commands = [key for key in module if key != "__meta__"]

    text = (
        f"{TOP}\n"
        f"{ITEM} <b>{module_name.title()}</b> · <code>{module_type}</code>\n"
        f"{ITEM} <b>{tr('version')}:</b> <code>{meta.get('version', 'unknown')}</code>\n"
        f"{ITEM} <b>{tr('description')}:</b> <i>{meta.get('description', '-')}</i>\n"
        f"{ITEM} <b>{tr('file')}:</b> <code>{module_path}</code>\n"
        f"{ITEM} <b>{tr('status')}:</b> <code>{_status(module_name)}</code>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('commands')}:</b> <code>{len(commands)}</code>\n"
    )

    for command in commands[:8]:
        text += f"{BRANCH} <code>{prefix}{command.split()[0]}</code>\n"

    if len(commands) > 8:
        text += f"{BRANCH} ...\n"

    return text + BOT


def _index_markup(page: int = 0) -> InlineKeyboardMarkup:
    page = _normalize_page(page)
    names = _module_names()
    start = page * PAGE_SIZE
    shown = names[start:start + PAGE_SIZE]
    rows = [
        [InlineKeyboardButton(name.title(), callback_data=f"mm:module:{name}")]
        for name in shown
    ]

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(tr("btn.prev"), callback_data=f"mm:page:{page - 1}"))
    if page + 1 < _page_count():
        nav.append(InlineKeyboardButton(tr("btn.next"), callback_data=f"mm:page:{page + 1}"))
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(rows)


def _module_markup(module_name: str) -> InlineKeyboardMarkup:
    rows = []

    if _is_disabled(module_name):
        rows.append([InlineKeyboardButton(tr("btn.enable"), callback_data=f"mm:enable:{module_name}")])
    elif not _is_protected(module_name):
        rows.append([InlineKeyboardButton(tr("btn.disable"), callback_data=f"mm:disable:{module_name}")])

    if _module_path(module_name):
        rows.append([InlineKeyboardButton(tr("btn.send"), switch_inline_query_current_chat=f"sendmod {module_name}")])

    rows.append([InlineKeyboardButton(tr("btn.back"), callback_data="mm:page:0")])

    return InlineKeyboardMarkup(rows)


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


def _register_manager_handlers(app: Client, owner_id: int) -> bool:
    global _handlers_registered, _owner_id

    bot = getattr(app, "bot", None)
    if not bot:
        return False

    _owner_id = owner_id

    if _handlers_registered:
        return True

    _handlers_registered = True

    @bot.on_callback_query(filters.regex(r"^mm:"))
    async def manager_callback(client, callback):
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

            if action == "module":
                await _edit_inline_or_message(
                    client,
                    callback,
                    _format_module(value),
                    _module_markup(value),
                )
                await callback.answer()
                return

            if action == "disable":
                if _is_protected(value):
                    await callback.answer(tr("protected_alert"), show_alert=True)
                    return

                disabled = _disabled_modules()
                disabled.add(value)
                _set_disabled_modules(disabled)
                await _edit_inline_or_message(
                    client,
                    callback,
                    f"<b>{tr('disabled_alert', module=value)}</b>",
                )
                await callback.answer()
                restart()
                return

            if action == "enable":
                disabled = _disabled_modules()
                disabled.discard(value)
                _set_disabled_modules(disabled)
                await _edit_inline_or_message(
                    client,
                    callback,
                    f"<b>{tr('enabled_alert', module=value)}</b>",
                )
                await callback.answer()
                restart()
                return

        except errors.MessageNotModified:
            await callback.answer()
        except Exception as e:
            await callback.answer(str(e), show_alert=True)

    return True


@inline_command("mm", tr("meta.description"))
@inline_command("manager", tr("meta.description"))
@inline_command("modules", tr("meta.description"))
async def inline_modules(app: Client, query, args):
    _register_manager_handlers(app, query.from_user.id)
    module_name = args.strip().lower()

    if module_name:
        text = _format_module(module_name)
        markup = _module_markup(module_name) if module_name in modules_help else _index_markup()
    else:
        text = _format_index()
        markup = _index_markup()

    return [
        InlineQueryResultArticle(
            title=tr("title"),
            description=module_name or tr("subtitle"),
            input_message_content=InputTextMessageContent(text),
            reply_markup=markup,
        )
    ]


@Client.on_message(filters.command(["modules", "mods", "mm", "manager"], prefix) & filters.me)
async def module_manager_cmd(client: Client, message: Message):
    if not _register_manager_handlers(client, message.from_user.id):
        await message.edit(tr("no_bot"))
        return

    query = "modules"
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


modules_help["module_manager"] = {
    "__meta__": {
        "version": "1.0.0",
        "description": tr.lazy("meta.description"),
        "pic": "https://i.ibb.co/FbNycfVQ/loader.png",
    },
    "modules/mods/mm/manager [module]": tr.lazy("help.manager"),
}
