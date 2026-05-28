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

from utils.db import db
from utils.i18n import Translator, available_langs, get_lang, set_lang
from utils.inline import inline_command
from utils.misc import modules_help, prefix
from utils.scripts import restart


strings = {
    "ru": {
        "title": "Настройки YuMo",
        "subtitle": "центр управления",
        "prefix": "Префикс",
        "language": "Язык",
        "modules": "Модулей",
        "commands": "Команд",
        "hint": "Выбери действие кнопками ниже.",
        "no_bot": "<b>Inline-бот не запущен.</b>\nДобавь <code>bot_token</code> в конфиг, чтобы кнопки работали.",
        "inline_error": "<b>Не удалось открыть inline-меню:</b> <code>{error}</code>",
        "inline_empty": "<b>Inline-бот не вернул меню настроек.</b>",
        "prefix_set": "Префикс изменен на {prefix}. Перезапускаюсь...",
        "lang_set": "Язык изменен на {lang}",
        "unknown_lang": "Неизвестный язык: {lang}",
        "owner_only": "Эта панель не для тебя.",
        "refreshed": "Панель обновлена",
        "restarting": "Перезапускаюсь...",
        "btn.refresh": "Обновить",
        "btn.restart": "Рестарт",
        "section.prefix": "Префикс",
        "section.lang": "Язык",
        "meta.description": "Панель настроек YuMo с кнопками",
        "help.settings": "открыть панель настроек с кнопками.",
    },
    "en": {
        "title": "YuMo Settings",
        "subtitle": "control center",
        "prefix": "Prefix",
        "language": "Language",
        "modules": "Modules",
        "commands": "Commands",
        "hint": "Choose an action with the buttons below.",
        "no_bot": "<b>Inline bot is not running.</b>\nAdd <code>bot_token</code> to config to use buttons.",
        "inline_error": "<b>Failed to open inline menu:</b> <code>{error}</code>",
        "inline_empty": "<b>Inline bot did not return the settings menu.</b>",
        "prefix_set": "Prefix changed to {prefix}. Restarting...",
        "lang_set": "Language changed to {lang}",
        "unknown_lang": "Unknown language: {lang}",
        "owner_only": "This panel is not yours.",
        "refreshed": "Panel refreshed",
        "restarting": "Restarting...",
        "btn.refresh": "Refresh",
        "btn.restart": "Restart",
        "section.prefix": "Prefix",
        "section.lang": "Language",
        "meta.description": "Button settings panel for YuMo",
        "help.settings": "open the button settings panel.",
    },
}

tr = Translator("settings", strings)

TOP = "╭─────────────────────"
MID = "├─────────────────────"
BOT = "╰─────────────────────"
ITEM = "│"
PREFIXES = [".", "!", "/", "#", "?", ","]
_handlers_registered = False
_owner_id = None


def _command_count() -> int:
    return sum(
        len([key for key in module if key != "__meta__"])
        for module in modules_help.values()
    )


def _panel_text() -> str:
    current_prefix = db.get("core.main", "prefix", prefix)
    return (
        f"{TOP}\n"
        f"{ITEM} <b>{tr('title')}</b> · <i>{tr('subtitle')}</i>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('prefix')}:</b> <code>{current_prefix}</code>\n"
        f"{ITEM} <b>{tr('language')}:</b> <code>{get_lang()}</code>\n"
        f"{ITEM} <b>{tr('modules')}:</b> <code>{len(modules_help)}</code>\n"
        f"{ITEM} <b>{tr('commands')}:</b> <code>{_command_count()}</code>\n"
        f"{MID}\n"
        f"{ITEM} <i>{tr('hint')}</i>\n"
        f"{BOT}"
    )


def _button(label: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(label, callback_data=f"settings:{data}")


def _panel_markup() -> InlineKeyboardMarkup:
    current_prefix = db.get("core.main", "prefix", prefix)
    current_lang = get_lang()

    prefix_buttons = [
        _button(
            f"{'* ' if pref == current_prefix else ''}{pref}",
            f"prefix:{pref}",
        )
        for pref in PREFIXES
    ]
    lang_buttons = [
        _button(
            f"{'* ' if lang == current_lang else ''}{lang}",
            f"lang:{lang}",
        )
        for lang in available_langs()
    ]

    return InlineKeyboardMarkup(
        [
            [_button(tr("section.prefix"), "noop")],
            prefix_buttons[:3],
            prefix_buttons[3:],
            [_button(tr("section.lang"), "noop")],
            lang_buttons,
            [
                _button(tr("btn.refresh"), "refresh"),
                _button(tr("btn.restart"), "restart"),
            ],
        ]
    )


def _register_settings_handlers(app: Client, owner_id: int) -> bool:
    global _handlers_registered, _owner_id

    bot = getattr(app, "bot", None)
    if not bot:
        return False

    _owner_id = owner_id

    if _handlers_registered:
        return True

    _handlers_registered = True

    @bot.on_callback_query(filters.regex(r"^settings:"))
    async def settings_callback(_, callback):
        if _owner_id and callback.from_user.id != _owner_id:
            await callback.answer(tr("owner_only"), show_alert=True)
            return

        action = callback.data.split(":", 1)[1]

        try:
            if action == "noop":
                await callback.answer()
                return

            if action == "refresh":
                await callback.message.edit_text(
                    _panel_text(),
                    reply_markup=_panel_markup(),
                    disable_web_page_preview=True,
                )
                await callback.answer(tr("refreshed"))
                return

            if action == "restart":
                await callback.message.edit_text(f"<b>{tr('restarting')}</b>")
                await callback.answer()
                restart()
                return

            kind, value = action.split(":", 1)

            if kind == "lang":
                if value not in available_langs():
                    await callback.answer(
                        tr("unknown_lang", lang=value),
                        show_alert=True,
                    )
                    return

                set_lang(value)
                await callback.message.edit_text(
                    _panel_text(),
                    reply_markup=_panel_markup(),
                    disable_web_page_preview=True,
                )
                await callback.answer(tr("lang_set", lang=value))
                return

            if kind == "prefix":
                db.set("core.main", "prefix", value)
                await callback.message.edit_text(
                    f"<b>{tr('prefix_set', prefix=value)}</b>"
                )
                await callback.answer()
                restart()
                return

        except errors.MessageNotModified:
            await callback.answer(tr("refreshed"))
        except Exception as e:
            await callback.answer(str(e), show_alert=True)

    return True


@inline_command("settings", tr("meta.description"))
async def inline_settings(app: Client, query, args):
    _register_settings_handlers(app, query.from_user.id)

    return [
        InlineQueryResultArticle(
            title=tr("title"),
            description=tr("subtitle"),
            input_message_content=InputTextMessageContent(_panel_text()),
            reply_markup=_panel_markup(),
        )
    ]


@Client.on_message(filters.command(["settings", "cfg", "config"], prefix) & filters.me)
async def settings_cmd(client: Client, message: Message):
    if not _register_settings_handlers(client, message.from_user.id):
        await message.edit(tr("no_bot"))
        return

    try:
        bot_me = await client.bot.get_me()
        results = await client.get_inline_bot_results(bot_me.username, "settings")

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


modules_help["settings"] = {
    "__meta__": {
        "version": "1.0.0",
        "description": tr.lazy("meta.description"),
        "pic": "https://i.ibb.co/Q7tP0Y6z/prefix.png",
    },
    "settings/cfg/config": tr.lazy("help.settings"),
}
